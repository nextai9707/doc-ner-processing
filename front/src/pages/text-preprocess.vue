<template>
	<div class="text-preprocess-container">
		<el-card shadow="never" class="main-card">
			<template #header>
				<div class="card-header">
					<span class="card-title">📝 文本预处理</span>
					<span class="card-subtitle">分词纠错、噪声过滤、去重清洗、支持多线程批量处理</span>
				</div>
			</template>

			<!-- 文档选择 -->
			<div class="section">
				<h3>选择文档（支持多选批量处理）</h3>
				<el-select
					v-model="selectedDocumentIds"
					placeholder="请选择要处理的文档"
					style="width: 100%"
					multiple
					collapse-tags
					collapse-tags-tooltip
					@change="onDocumentChange"
				>
					<el-option
						v-for="doc in documentList"
						:key="doc.id"
						:label="doc.original_filename"
						:value="doc.id"
						:disabled="!doc.content && doc.status !== 'parsed' && doc.status !== 'uploaded'"
					>
						<span>{{ doc.original_filename }}</span>
						<span style="float: right; color: #8492a6; font-size: 13px">
							{{ doc.file_type.toUpperCase() }} - {{ getStatusText(doc.status) }}
						</span>
					</el-option>
				</el-select>
				<div class="selection-info" v-if="selectedDocumentIds.length > 0">
					<el-tag type="primary">已选择 {{ selectedDocumentIds.length }} 个文档</el-tag>
					<el-tag v-if="selectedDocumentIds.length > 1" type="warning">将使用多线程批量处理</el-tag>
				</div>
			</div>

			<!-- 预处理配置 -->
			<div class="section" v-if="selectedDocumentIds.length > 0">
				<h3>预处理配置</h3>
				<el-form :model="preprocessConfig" label-width="160px">
					<el-row :gutter="20">
						<el-col :span="12">
							<el-form-item label="中文分词">
								<el-switch v-model="preprocessConfig.enable_segmentation" />
							</el-form-item>
						</el-col>
						<el-col :span="12">
							<el-form-item label="分词纠错">
								<el-switch v-model="preprocessConfig.enable_correction" />
							</el-form-item>
						</el-col>
					</el-row>
					<el-row :gutter="20">
						<el-col :span="12">
							<el-form-item label="去除停用词">
								<el-switch v-model="preprocessConfig.remove_stopwords" />
							</el-form-item>
						</el-col>
						<el-col :span="12">
							<el-form-item label="页眉页脚过滤">
								<el-switch v-model="preprocessConfig.remove_headers_footers" />
							</el-form-item>
						</el-col>
					</el-row>
					<el-row :gutter="20">
						<el-col :span="12">
							<el-form-item label="乱码/特殊符号过滤">
								<el-switch v-model="preprocessConfig.remove_garbage" />
							</el-form-item>
						</el-col>
						<el-col :span="12">
							<el-form-item label="段落去重清洗">
								<el-switch v-model="preprocessConfig.remove_duplicates" />
							</el-form-item>
						</el-col>
					</el-row>
					<el-row :gutter="20">
    <el-col :span="12">
        <el-form-item label="URL/HTML清理">
            <el-switch v-model="preprocessConfig.remove_urls" />
        </el-form-item>
    </el-col>
    <el-col :span="12">
        <el-form-item label="字符规范化">
            <el-switch v-model="preprocessConfig.normalize_chars" />
            <el-tooltip content="全角转半角、特殊字符规范" placement="top">
                <el-icon style="margin-left: 6px"><InfoFilled /></el-icon>
            </el-tooltip>
        </el-form-item>
    </el-col>
</el-row>
<el-row :gutter="20">
    <el-col :span="12">
        <el-form-item label="短行过滤">
            <el-switch v-model="preprocessConfig.remove_short_lines" />
        </el-form-item>
    </el-col>
    <el-col :span="12">
        <el-form-item label="最小行长度" v-if="preprocessConfig.remove_short_lines">
            <el-input-number v-model="preprocessConfig.min_line_length" :min="1" :max="100" />
        </el-form-item>
    </el-col>
</el-row>
					<el-form-item label="词性标注">
						<el-switch v-model="preprocessConfig.pos_tagging" />
					</el-form-item>
					<el-form-item label="正则匹配">
						<el-input
							v-model="preprocessConfig.regex_pattern"
							placeholder="输入正则表达式（可选）"
						/>
					</el-form-item>
					<el-form-item>
						<el-button type="primary" @click="startPreprocess" :loading="processing">
							开始预处理
							<span v-if="selectedDocumentIds.length > 1">（批量）</span>
						</el-button>
					</el-form-item>
				</el-form>
			</div>

			<!-- 处理进度 -->
			<div class="section" v-if="processing && selectedDocumentIds.length > 1">
				<h3>处理进度</h3>
				<el-progress :percentage="progressPercent" :stroke-width="20" status="success" />
				<div class="progress-detail">
					<el-tag v-for="(status, idx) in processingStatus" :key="idx" :type="status.type">
						{{ status.filename }}: {{ status.message }}
					</el-tag>
				</div>
			</div>

			<!-- 批量处理结果 -->
			<div class="section" v-if="batchResults.length > 0">
				<h3>批量处理结果</h3>
				<el-table :data="batchResults" stripe border>
					<el-table-column prop="filename" label="文件名" min-width="180" />
					<el-table-column prop="status" label="状态" width="100">
						<template #default="{ row }">
							<el-tag :type="row.status === 'success' ? 'success' : 'danger'">
								{{ row.status === 'success' ? '成功' : '失败' }}
							</el-tag>
						</template>
					</el-table-column>
					<el-table-column prop="message" label="信息" min-width="200" />
					<el-table-column label="操作" width="120">
						<template #default="{ row }">
							<el-button size="small" type="primary" @click="viewBatchResult(row)" v-if="row.status === 'success'">
								查看
							</el-button>
						</template>
					</el-table-column>
				</el-table>
			</div>

			<!-- 处理结果详情 -->
			<div class="section" v-if="preprocessResult">
				<h3>处理结果详情</h3>
				<el-tabs v-model="activeTab">
				<el-tab-pane label="🔄 处理过程日志" name="logs" v-if="preprocessResult.process_logs?.length">
    <div class="process-timeline">
        <el-timeline>
            <el-timeline-item
                v-for="(log, idx) in preprocessResult.process_logs"
                :key="idx"
                :type="getLogType(log.step)"
                :icon="getLogIcon(log.step)"
                :timestamp="formatLogTime(log.timestamp)"
                placement="top"
                :hollow="log.step === 'init' || log.step === 'done'"
            >
                <el-card class="log-card">
                    <h4 class="log-title">
                        <span class="log-step-tag">{{ log.step }}</span>
                        {{ log.name }}
                    </h4>
                    <p class="log-detail">{{ log.detail }}</p>
                    <!-- 纠错明细展开 -->
                    <div v-if="log.corrections && log.corrections.length" class="corrections-list">
                        <el-tag
                            v-for="(c, i) in log.corrections"
                            :key="i"
                            type="warning"
                            size="small"
                            style="margin: 2px"
                        >
                            {{ c.wrong }} → {{ c.right }}
                        </el-tag>
                    </div>
                </el-card>
            </el-timeline-item>
        </el-timeline>
    </div>
</el-tab-pane>

<!-- 同时增加纠错明细标签页 -->
<el-tab-pane label="✏️ 纠错明细" name="corrections" v-if="preprocessResult.corrections?.length">
    <el-table :data="preprocessResult.corrections" stripe border size="small">
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="wrong" label="错词" width="120">
            <template #default="{ row }"><el-tag type="danger">{{ row.wrong }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="right" label="正词" width="120">
            <template #default="{ row }"><el-tag type="success">{{ row.right }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="position" label="出现位置" width="120" />
    </el-table>
</el-tab-pane>
					<el-tab-pane label="清洗后文本" name="cleaned">
						<div class="result-content">
							<div class="text-preview">
								<p class="preview-label">清洗后文本预览：</p>
								<pre>{{ preprocessResult.cleaned_text }}</pre>
							</div>
							<div class="filter-info" v-if="preprocessResult.removed_headers">
								<el-alert :title="preprocessResult.removed_headers" type="info" show-icon />
							</div>
							<div class="filter-info" v-if="preprocessResult.removed_garbage">
								<el-alert :title="preprocessResult.removed_garbage" type="info" show-icon />
							</div>
							<div class="filter-info" v-if="preprocessResult.deduplicated_text">
								<el-alert title="已执行段落去重" type="success" show-icon />
							</div>
						</div>
					</el-tab-pane>
					<el-tab-pane label="分词纠错结果" name="segmentation" v-if="preprocessResult.segmented_words?.length">
						<div class="result-content">
							<div class="corrected-text" v-if="preprocessResult.corrected_text">
								<p class="preview-label">纠错后文本预览：</p>
								<pre>{{ preprocessResult.corrected_text }}</pre>
							</div>
							<el-divider />
							<el-tag
								v-for="(word, idx) in preprocessResult.segmented_words"
								:key="idx"
								style="margin: 4px"
							>
								{{ word }}
							</el-tag>
						</div>
					</el-tab-pane>
					<el-tab-pane label="词性标注" name="pos" v-if="preprocessResult.pos_tags?.length">
						<div class="result-content">
							<el-tag
								v-for="(item, idx) in preprocessResult.pos_tags"
								:key="idx"
								:type="getPosTagType(item.pos)"
								style="margin: 4px"
							>
								{{ item.word }}/{{ item.pos }}
							</el-tag>
						</div>
					</el-tab-pane>
					<el-tab-pane label="正则匹配" name="regex" v-if="preprocessResult.regex_matches?.length">
						<div class="result-content">
							<div v-for="(match, idx) in preprocessResult.regex_matches" :key="idx" class="match-item">
								{{ match }}
							</div>
						</div>
					</el-tab-pane>
					<el-tab-pane label="统计信息" name="stats">
						<el-descriptions :column="2" border>
							<el-descriptions-item label="原始长度">
								{{ preprocessResult.stats?.original_length || 0 }}
							</el-descriptions-item>
							<el-descriptions-item label="清洗后长度">
								{{ preprocessResult.stats?.cleaned_length || 0 }}
							</el-descriptions-item>
							<el-descriptions-item label="压缩比例">
								{{ preprocessResult.stats?.reduction_ratio || 0 }}%
							</el-descriptions-item>
							<el-descriptions-item label="总词数">
								{{ preprocessResult.stats?.total_words || 0 }}
							</el-descriptions-item>
							<el-descriptions-item label="唯一词数">
								{{ preprocessResult.stats?.unique_words || 0 }}
							</el-descriptions-item>
							<el-descriptions-item label="正则匹配数">
								{{ preprocessResult.stats?.regex_matches_count || 0 }}
							</el-descriptions-item>
						</el-descriptions>
					</el-tab-pane>
				</el-tabs>
			</div>
		</el-card>
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { adminRequest } from '@/composables/adminRequest'

const selectedDocumentIds = ref<number[]>([])
const documentList = ref<any[]>([])
const processing = ref(false)
const activeTab = ref('cleaned')
const preprocessResult = ref<any>(null)
const batchResults = ref<any[]>([])
const progressPercent = ref(0)
const processingStatus = ref<any[]>([])
const getLogType = (step: string): string => {
    const map: Record<string, string> = {
        init: 'primary', done: 'success',
        remove_headers_footers: 'warning', remove_garbage: 'warning',
        remove_duplicates: 'warning', remove_short_lines: 'warning',
        remove_urls: 'warning', normalize_chars: 'info',
        correct_words: 'danger', segmentation: 'success',
        remove_stopwords: 'info', pos_tagging: 'success', regex: 'primary'
    }
    return map[step] || 'info'
}
const getLogIcon = (step: string) => {
    // 返回 Element Plus 图标组件名（在 main.ts 已全局注册）
    const map: Record<string, string> = {
        init: 'VideoPlay', done: 'CircleCheck',
        correct_words: 'EditPen', segmentation: 'Connection',
    }
    return map[step] || ''
}
const formatLogTime = (ts: string): string => {
    if (!ts) return ''
    return new Date(ts).toLocaleTimeString('zh-CN')
}
const preprocessConfig = reactive({
    enable_segmentation: true,
    enable_correction: true,
    remove_stopwords: true,
    remove_headers_footers: true,
    remove_garbage: true,
    remove_duplicates: true,
    remove_urls: false,           // ⭐ 新增
    normalize_chars: false,       // ⭐ 新增
    remove_short_lines: false,    // ⭐ 新增
    min_line_length: 5,           // ⭐ 新增
    pos_tagging: false,
    regex_pattern: ''
})

const getStatusText = (status: string): string => {
	const statusMap: Record<string, string> = {
		'uploaded': '已上传',
		'parsed': '已解析',
		'processed': '已处理',
		'error': '处理失败'
	}
	return statusMap[status] || status
}

const getPosTagType = (pos: string): string => {
	if (pos.startsWith('n')) return 'success'
	if (pos.startsWith('v')) return 'warning'
	if (pos.startsWith('a')) return 'danger'
	return 'info'
}

const onDocumentChange = () => {
	preprocessResult.value = null
	batchResults.value = []
}

const fetchDocuments = async () => {
	try {
		const res: any = await adminRequest.get('/api/document/list?limit=100')
		if (res?.data?.list) {
			documentList.value = res.data.list
		}
	} catch (e) {
		ElMessage.error('获取文档列表失败')
	}
}

const startPreprocess = async () => {
	if (selectedDocumentIds.value.length === 0) {
		ElMessage.warning('请先选择文档')
		return
	}

	processing.value = true
	progressPercent.value = 0
	processingStatus.value = []
	batchResults.value = []
	preprocessResult.value = null

	try {
		const res: any = await adminRequest.post('/api/text/preprocess', {
			document_ids: selectedDocumentIds.value,
			config: preprocessConfig
		})

		if (res?.data?.results) {
			batchResults.value = res.data.results
			const successResults = res.data.results.filter((r: any) => r.status === 'success')
			if (successResults.length > 0) {
				preprocessResult.value = successResults[0].result
			}
			ElMessage.success(`预处理完成，成功处理 ${res.data.success_count}/${res.data.total} 个文档`)
		} else {
			preprocessResult.value = res.data
			ElMessage.success('预处理完成')
		}
	} catch (e: any) {
		ElMessage.error(e?.message || '预处理失败')
	} finally {
		processing.value = false
		progressPercent.value = 100
	}
}

const viewBatchResult = (row: any) => {
	if (row.result) {
		preprocessResult.value = row.result
		activeTab.value = 'cleaned'
	}
}

onMounted(() => {
	fetchDocuments()
})
</script>

<style scoped>
.text-preprocess-container {
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

.selection-info {
	margin-top: 10px;
	display: flex;
	gap: 10px;
}

.result-content {
	max-height: 500px;
	overflow-y: auto;
	padding: 20px;
	background: #f5f5f5;
	border-radius: 4px;
	min-height: 200px;
}

.text-preview pre {
	white-space: pre-wrap;
	word-wrap: break-word;
	font-family: 'Courier New', monospace;
	font-size: 14px;
	line-height: 1.6;
	background: white;
	padding: 15px;
	border-radius: 4px;
	max-height: 300px;
	overflow-y: auto;
}

.preview-label {
	font-weight: 600;
	color: #2c3e50;
	margin-bottom: 10px;
}

.corrected-text pre {
	white-space: pre-wrap;
	word-wrap: break-word;
	font-family: 'Courier New', monospace;
	font-size: 14px;
	line-height: 1.6;
	background: #e8f5e9;
	padding: 15px;
	border-radius: 4px;
	max-height: 200px;
	overflow-y: auto;
}

.filter-info {
	margin-top: 10px;
}

.match-item {
	padding: 8px;
	margin-bottom: 8px;
	background: white;
	border-radius: 4px;
	border-left: 3px solid #3498db;
}

.progress-detail {
	margin-top: 15px;
	display: flex;
	flex-wrap: wrap;
	gap: 8px;
}
.process-timeline {
    padding: 20px;
    background: #fafafa;
    border-radius: 8px;
    max-height: 600px;
    overflow-y: auto;
}
.log-card {
    border-radius: 6px;
}
.log-title {
    margin: 0 0 8px 0;
    color: #2c3e50;
    font-size: 14px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 8px;
}
.log-step-tag {
    background: #ecf5ff;
    color: #409eff;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-family: 'Courier New', monospace;
}
.log-detail {
    margin: 0;
    color: #606266;
    font-size: 13px;
    line-height: 1.6;
}
.corrections-list {
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px dashed #e4e7ed;
}
</style>
