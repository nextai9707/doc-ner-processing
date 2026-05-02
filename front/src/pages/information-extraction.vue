<template>
	<div class="extraction-container">
		<el-card class="main-card">
			<template #header>
				<div class="card-header">
					<span class="card-title">🔍 信息抽取</span>
					<span class="card-subtitle">基于规则和算法的双重抽取模式</span>
				</div>
			</template>

			<!-- 文档选择 -->
			<div class="section">
				<h3>选择文档</h3>
<el-select
    v-model="selectedDocumentId"
    placeholder="请选择要处理的文档（无需先解析，会自动处理）"
    style="width: 100%"
    filterable
    @change="onDocumentChange"
>
    <el-option-group label="✅ 已解析（可直接抽取）" v-if="parsedDocs.length">
        <el-option
            v-for="doc in parsedDocs"
            :key="doc.id"
            :label="doc.original_filename"
            :value="doc.id"
        >
            <span style="float: left">{{ doc.original_filename }}</span>
            <span style="float: right; color: #67c23a; font-size: 12px">
                {{ doc.file_type?.toUpperCase() }} · 已解析
            </span>
        </el-option>
    </el-option-group>
    <el-option-group label="⏳ 已上传（点击后自动解析）" v-if="unparsedDocs.length">
        <el-option
            v-for="doc in unparsedDocs"
            :key="doc.id"
            :label="doc.original_filename"
            :value="doc.id"
        >
            <span style="float: left">{{ doc.original_filename }}</span>
            <span style="float: right; color: #e6a23c; font-size: 12px">
                {{ doc.file_type?.toUpperCase() }} · 未解析
            </span>
        </el-option>
    </el-option-group>
</el-select>
<el-button
    size="small"
    type="primary"
    plain
    @click="fetchDocuments"
    style="margin-top: 8px"
>
    <el-icon><Refresh /></el-icon>
    刷新文档列表
</el-button>
			</div>

			<!-- 抽取配置 -->
			<div class="section" v-if="selectedDocumentId">
				<h3>抽取配置</h3>
				<el-form :model="config" label-width="120px">
					<el-form-item label="抽取模式">
						<el-radio-group v-model="config.extraction_type">
							<el-radio label="rule">规则抽取</el-radio>
							<el-radio label="algorithm">算法抽取</el-radio>
							<el-radio label="both">双重模式</el-radio>
						</el-radio-group>
					</el-form-item>
					<el-form-item label="抽取字段">
						<el-checkbox-group v-model="config.fields">
							<el-checkbox label="date">日期</el-checkbox>
							<el-checkbox label="money">金额</el-checkbox>
							<el-checkbox label="person">人名</el-checkbox>
							<el-checkbox label="organization">机构</el-checkbox>
							<el-checkbox label="location">地点</el-checkbox>
						</el-checkbox-group>
					</el-form-item>
					<el-form-item>
						<el-button type="primary" @click="extract" :loading="processing">
							开始抽取
						</el-button>
					</el-form-item>
				</el-form>
			</div>

			<!-- 抽取结果 -->
			<div class="section" v-if="result">
				<h3>抽取结果</h3>
				<el-table :data="resultTable" stripe>
					<el-table-column prop="field_name" label="字段名" width="150" />
					<el-table-column prop="field_value" label="字段值" min-width="200" />
					<el-table-column prop="extraction_type" label="抽取方式" width="120">
						<template #default="{ row }">
							<el-tag :type="row.extraction_type === 'rule' ? 'success' : 'warning'">
								{{ row.extraction_type === 'rule' ? '规则' : '算法' }}
							</el-tag>
						</template>
					</el-table-column>
					<el-table-column prop="confidence" label="置信度" width="120">
						<template #default="{ row }">
							{{ row.confidence ? (row.confidence * 100).toFixed(1) + '%' : '-' }}
						</template>
					</el-table-column>
				</el-table>
			</div>
		</el-card>
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { adminRequest } from '@/composables/adminRequest'
import { onActivated } from 'vue'

const selectedDocumentId = ref<number | null>(null)
const documentList = ref<any[]>([])
const processing = ref(false)
const result = ref<any>(null)

const config = reactive({
    extraction_type: 'both',
    fields: ['date', 'money']
})

const resultTable = computed(() => {
    if (!result.value || !result.value.extractions) return []
    return result.value.extractions
})

// ⭐ 已解析的文档（parsed / processed 都算）
const parsedDocs = computed(() =>
    documentList.value.filter((d: any) => d.status === 'parsed' || d.status === 'processed')
)
// ⭐ 还没解析的文档（uploaded）
const unparsedDocs = computed(() =>
    documentList.value.filter((d: any) => d.status === 'uploaded')
)

const onDocumentChange = () => {
    result.value = null
}

// ⭐ 修复：不再做严格过滤，全量加载，由模板分组展示
const fetchDocuments = async () => {
    try {
        const res: any = await adminRequest.get('/api/document/list?limit=100')
        if (res?.data?.list) {
            // 排除处理失败的文档，其余全部显示
            documentList.value = res.data.list.filter((doc: any) => doc.status !== 'error')
        }
    } catch (e) {
        ElMessage.error('获取文档列表失败')
    }
}

// ⭐ 自动解析未解析的文档
const ensureParsed = async (docId: number): Promise<boolean> => {
    const doc = documentList.value.find((d: any) => d.id === docId)
    if (!doc) return false
    if (doc.status === 'parsed' || doc.status === 'processed') return true

    try {
        ElMessage.info('文档尚未解析，正在自动解析...')
        await adminRequest.post(`/api/document/${docId}/parse`)
        doc.status = 'parsed'  // 本地同步状态
        ElMessage.success('解析完成')
        return true
    } catch (e: any) {
        ElMessage.error('文档解析失败：' + (e?.message || '未知错误'))
        return false
    }
}

const extract = async () => {
    if (!selectedDocumentId.value) {
        ElMessage.warning('请先选择文档')
        return
    }
    if (config.fields.length === 0) {
        ElMessage.warning('请至少选择一个抽取字段')
        return
    }

    processing.value = true
    try {
        // ⭐ 关键：先确保文档已解析
        const ok = await ensureParsed(selectedDocumentId.value)
        if (!ok) {
            processing.value = false
            return
        }

        const res: any = await adminRequest.post('/api/extraction/extract', {
            document_id: selectedDocumentId.value,
            config: config
        })
        result.value = res.data
        ElMessage.success('抽取完成')
    } catch (e: any) {
        ElMessage.error(e?.message || '抽取失败')
    } finally {
        processing.value = false
    }
}

onMounted(() => {
	fetchDocuments()
})

// ⭐ 当用户重新进入此页面时刷新列表（vue-router 缓存的页面）
onActivated(() => {
    fetchDocuments()
})
</script>

<style scoped>
.extraction-container {
	padding: 20px;
}

.main-card {
	border-radius: 8px;
}

.card-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.card-title {
	font-size: 18px;
	font-weight: 600;
	color: #2c3e50;
}

.card-subtitle {
	font-size: 14px;
	color: #7f8c8d;
}

.section {
	margin-bottom: 30px;
}

.section h3 {
	margin-bottom: 15px;
	color: #2c3e50;
	font-size: 16px;
}
</style>

