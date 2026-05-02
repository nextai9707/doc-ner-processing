<template>
	<div class="batch-processing-container">
		<el-card class="main-card">
			<template #header>
				<div class="card-header">
					<span class="card-title">⚡ 批量处理</span>
					<span class="card-subtitle">大规模批量处理与清洗</span>
				</div>
			</template>

			<!-- 批量上传 -->
			<div class="section">
				<h3>批量上传文档</h3>
				<el-upload
					class="upload-area"
					drag
					:action="uploadUrl"
					:headers="uploadHeaders"
					:on-success="handleUploadSuccess"
					:before-upload="beforeUpload"
					multiple
					accept=".txt,.doc,.docx,.pdf"
				>
					<el-icon class="el-icon--upload">
						<upload-filled/>
					</el-icon>
					<div class="el-upload__text">
						将文件拖到此处，或<em>点击上传</em>
					</div>
					<template #tip>
						<div class="el-upload__tip">
							支持批量上传多个文件
						</div>
					</template>
				</el-upload>
			</div>

			<!-- 批量处理配置 -->
			<div class="section">
				<h3>处理配置</h3>
				<el-form :model="config" label-width="120px">
					<el-form-item label="处理类型">
<el-checkbox-group v-model="config.types">
    <el-checkbox label="parse">解析</el-checkbox>
    <el-checkbox label="preprocess">预处理</el-checkbox>
    <el-checkbox label="extract">信息抽取</el-checkbox>
    <el-checkbox label="keyword_summary">关键词与摘要</el-checkbox>
</el-checkbox-group>

<!-- 在处理类型下面新增：文档选择 + 子配置 -->
<el-form-item label="选择文档">
    <el-select v-model="selectedDocIds" multiple collapse-tags collapse-tags-tooltip
               placeholder="不选则自动处理本用户所有未处理文档（最多50个）"
               style="width: 100%">
        <el-option v-for="doc in documentList" :key="doc.id"
                   :label="doc.original_filename" :value="doc.id">
            <span>{{ doc.original_filename }}</span>
            <span style="float: right; color: #999; font-size: 12px">
                {{ doc.file_type?.toUpperCase() }} · {{ doc.status }}
            </span>
        </el-option>
    </el-select>
</el-form-item>
<el-form-item label="并发线程数">
    <el-input-number v-model="config.max_workers" :min="1" :max="8" />
    <span style="margin-left: 10px; color: #909399; font-size: 12px">
        建议 2-4，过高会占用服务器资源
    </span>
</el-form-item>

<!-- 关键词摘要子配置 -->
<el-form-item label="摘要长度" v-if="config.types.includes('keyword_summary')">
    <el-slider v-model="config.keyword_summary.summary_length" :min="100" :max="800"
               show-input style="width: 60%" />
</el-form-item>
<el-form-item label="抽取字段" v-if="config.types.includes('extract')">
    <el-checkbox-group v-model="config.extraction.fields">
        <el-checkbox label="date">日期</el-checkbox>
        <el-checkbox label="money">金额</el-checkbox>
        <el-checkbox label="email">邮箱</el-checkbox>
        <el-checkbox label="phone">电话</el-checkbox>
        <el-checkbox label="person">人名</el-checkbox>
        <el-checkbox label="organization">机构</el-checkbox>
        <el-checkbox label="location">地点</el-checkbox>
    </el-checkbox-group>
</el-form-item>
					</el-form-item>
					<el-form-item>
						<el-button type="primary" @click="startBatchProcess" :loading="processing">
							开始批量处理
						</el-button>
					</el-form-item>
				</el-form>
			</div>

			<!-- 处理进度 -->
			<div class="section" v-if="processing">
				<h3>处理进度</h3>
				<el-progress :percentage="progress" :status="progressStatus"/>
				<div class="progress-info">
					<span>已处理: {{ processedCount }} / {{ totalCount }}</span>
				</div>
			</div>

			<!-- 处理结果 -->
			<div class="section" v-if="results.length > 0">
				<h3>处理结果</h3>
				<el-table :data="results" stripe>
					<el-table-column prop="filename" label="文件名"/>
					<el-table-column prop="status" label="状态" width="120">
						<template #default="{ row }">
							<el-tag :type="row.status === 'success' ? 'success' : 'danger'">
								{{ row.status === 'success' ? '成功' : '失败' }}
							</el-tag>
						</template>
					</el-table-column>
					<el-table-column prop="message" label="消息"/>
				</el-table>
			</div>
		</el-card>
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { adminRequest } from '@/composables/adminRequest'
import userStore from '@/stores/userStore'

const user = userStore()
const processing = ref(false)
const progress = ref(0)
const progressStatus = ref<'success' | 'exception' | 'warning' | ''>('')
const processedCount = ref(0)
const totalCount = ref(0)
const results = ref<any[]>([])
const documentList = ref<any[]>([])
const selectedDocIds = ref<number[]>([])

const config = reactive({
    types: ['parse', 'preprocess'] as string[],
    max_workers: 4,
    preprocess: {
        enable_segmentation: true,
        enable_correction: true,
        remove_stopwords: true,
        remove_headers_footers: true,
        remove_garbage: true,
        remove_duplicates: true,
    },
    keyword_summary: {
        keyword: true,
        keyword_algorithm: 'tfidf',
        keyword_count: 20,
        summary: true,
        summary_length: 300,
    },
    extraction: {
        fields: ['date', 'money', 'email', 'phone'],
    },
})

const uploadUrl = computed(() => {
    const baseURL = import.meta.env.VITE_ADMIN_API_BASE_URL || ''
    return `${baseURL}/api/document/upload`
})
const uploadHeaders = computed(() => ({ token: user.userInfo?.token || '' }))

const beforeUpload = (file: File) => {
    const ok = file.name.endsWith('.txt') || file.name.endsWith('.docx') ||
               file.name.endsWith('.doc') || file.name.endsWith('.pdf')
    if (!ok) { ElMessage.error('不支持的文件格式!'); return false }
    return true
}
const handleUploadSuccess = () => {
    ElMessage.success('文件上传成功!')
    loadDocuments()
}

const loadDocuments = async () => {
    try {
        const res: any = await adminRequest.get('/api/document/list?limit=200')
        documentList.value = res?.data?.list || []
    } catch {}
}

const startBatchProcess = async () => {
    if (config.types.length === 0) {
        ElMessage.warning('请至少选择一种处理类型')
        return
    }
    processing.value = true
    progress.value = 0
    processedCount.value = 0
    totalCount.value = 0
    results.value = []

    try {
        const payload: any = { config: config }
        if (selectedDocIds.value.length > 0) {
            payload.document_ids = selectedDocIds.value
        }
        const res: any = await adminRequest.post('/api/batch/process', payload)
        results.value = res.data?.results || []
        totalCount.value = results.value.length
        processedCount.value = res.data?.success_count || 0
        if (totalCount.value > 0) {
            progress.value = Math.round((processedCount.value / totalCount.value) * 100)
            progressStatus.value = processedCount.value === totalCount.value ? 'success' : 'warning'
            ElMessage.success(`批量处理完成：成功 ${processedCount.value}/${totalCount.value}`)
        } else {
            ElMessage.warning('没有文档需要处理')
            progressStatus.value = 'exception'
        }
    } catch (e: any) {
        progressStatus.value = 'exception'
        ElMessage.error(e?.message || '批量处理失败')
    } finally {
        processing.value = false
    }
}

onMounted(() => { loadDocuments() })
</script>

<style scoped>
.batch-processing-container {
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

.progress-info {
	margin-top: 10px;
	color: #7f8c8d;
}
</style>

