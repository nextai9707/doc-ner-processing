<template>
    <div class="result-display-container">
        <el-card shadow="never" class="main-card">
            <template #header>
                <div class="card-header">
                    <span class="card-title">📊 结果可视化</span>
                    <span class="card-subtitle">所有处理结果的结构化展示与多格式导出</span>
                </div>
            </template>

            <!-- 筛选 + 搜索 -->
            <div class="filter-bar">
                <el-input
                    v-model="filterForm.keyword"
                    placeholder="🔍 搜索文档名/关键词/摘要内容..."
                    clearable
                    style="width: 300px"
                    @keyup.enter="loadResults"
                    @clear="loadResults"
                />
                <el-select v-model="filterForm.document_id" placeholder="按文档筛选" clearable
                           style="width: 240px" @change="loadResults">
                    <el-option v-for="doc in documentList" :key="doc.id"
                               :label="doc.original_filename" :value="doc.id" />
                </el-select>
                <el-select v-model="filterForm.task_type" placeholder="按类型筛选" clearable
                           style="width: 180px" @change="loadResults">
                    <el-option label="文本预处理" value="preprocess" />
                    <el-option label="关键词摘要" value="keyword_summary" />
                    <el-option label="信息抽取" value="extraction" />
                </el-select>
                <el-button type="primary" :icon="Refresh" @click="loadResults" :loading="loading">刷新</el-button>
                <el-radio-group v-model="layoutMode" style="margin-left: auto">
                    <el-radio-button label="card">卡片视图</el-radio-button>
                    <el-radio-button label="compact">紧凑视图</el-radio-button>
                </el-radio-group>
            </div>

            <!-- 主区域：每个结果一张卡片，所有数据直接铺开 -->
            <div v-loading="loading" class="results-area" :class="layoutMode">
                <el-empty v-if="results.length === 0 && !loading" description="暂无处理结果" />

                <div v-for="item in results" :key="item.task_id" class="result-card">
                    <!-- 卡片头 -->
                    <div class="result-card-header">
                        <div class="header-left">
                            <el-tag :type="getTaskTypeTag(item.task_type)" size="small">
                                {{ getTaskTypeText(item.task_type) }}
                            </el-tag>
                            <span class="doc-name">📄 {{ item.document_name }}</span>
                            <span class="result-time">{{ formatDateTime(item.created_at) }}</span>
                        </div>
                        <div class="header-right">
                            <el-button-group>
                                <el-button size="small" @click="exportResult(item.task_id, 'json')">JSON</el-button>
                                <el-button size="small" type="success" @click="exportResult(item.task_id, 'excel')">Excel</el-button>
                                <el-button size="small" type="warning" @click="exportResult(item.task_id, 'csv')">CSV</el-button>
                            </el-button-group>
                        </div>
                    </div>

                    <!-- 卡片体：根据 task_type 渲染不同的结构化视图 -->
                    <div class="result-card-body">
                        <!-- ===== 关键词摘要类型 ===== -->
                        <template v-if="item.task_type === 'keyword_summary'">
                            <!-- 关键词云/列表 -->
                            <div v-if="item.result.keywords?.length" class="kw-section">
                                <div class="section-title">🔑 关键词 Top {{ item.result.keywords.length }}</div>
                                <div class="kw-list">
                                    <el-tag
                                        v-for="(kw, i) in item.result.keywords.slice(0, layoutMode === 'compact' ? 10 : 30)"
                                        :key="i"
                                        :type="i < 3 ? 'danger' : i < 8 ? 'warning' : ''"
                                        :size="i < 5 ? 'large' : 'default'"
                                        :style="{fontSize: getKwFontSize(kw.score, item.result.keywords[0].score) + 'px'}"
                                        class="kw-tag"
                                    >
                                        {{ kw.word }}
                                        <span class="kw-score">{{ kw.score.toFixed(3) }}</span>
                                    </el-tag>
                                </div>
                            </div>
                            <!-- 摘要 -->
                            <div v-if="item.result.summary" class="summary-section">
                                <div class="section-title">
                                    📝 抽取式摘要
                                    <el-tag size="small" type="info">{{ item.result.summary_meta?.algorithm || 'TextRank' }}</el-tag>
                                    <el-tag size="small">{{ item.result.summary_length_actual }}/{{ item.result.summary_meta?.target_length }} 字符</el-tag>
                                </div>
                                <div class="summary-content">{{ item.result.summary }}</div>
                                <el-collapse v-if="item.result.summary_all_sentences?.length">
                                    <el-collapse-item title="🔍 查看 TextRank 句子打分详情">
                                        <div class="mini-sentence-list">
                                            <div v-for="(s, i) in getTopSentences(item.result, 10)" :key="i"
                                                 :class="['mini-sent', { selected: isSentenceSelected(item.result, s.index) }]">
                                                <strong>{{ s.score.toFixed(3) }}</strong>
                                                <span>{{ s.text }}</span>
                                            </div>
                                        </div>
                                    </el-collapse-item>
                                </el-collapse>
                            </div>
                        </template>

                        <!-- ===== 信息抽取类型 ===== -->
                        <template v-else-if="item.task_type === 'extraction'">
                            <div class="section-title">🔍 抽取结果（共 {{ getExtractions(item.result).length }} 条）</div>
                            <el-table :data="getExtractions(item.result)" stripe size="small" border
                                      max-height="400">
                                <el-table-column prop="field_name" label="字段" width="100">
                                    <template #default="{ row }">
                                        <el-tag size="small" :type="getFieldTypeTag(row.field_name)">
                                            {{ getFieldTypeLabel(row.field_name) }}
                                        </el-tag>
                                    </template>
                                </el-table-column>
                                <el-table-column prop="field_value" label="值" min-width="200">
                                    <template #default="{ row }">
                                        <el-link v-if="row.field_name === 'email'" :href="`mailto:${row.field_value}`">
                                            {{ row.field_value }}
                                        </el-link>
                                        <span v-else>{{ row.field_value }}</span>
                                    </template>
                                </el-table-column>
                                <el-table-column prop="extraction_type" label="方式" width="80">
                                    <template #default="{ row }">
                                        <el-tag size="small" :type="row.extraction_type === 'rule' ? 'primary' : 'success'">
                                            {{ row.extraction_type === 'rule' ? '规则' : '算法' }}
                                        </el-tag>
                                    </template>
                                </el-table-column>
                                <el-table-column prop="confidence" label="置信度" width="120">
                                    <template #default="{ row }">
                                        <el-progress :percentage="Math.round(row.confidence * 100)"
                                                     :stroke-width="6" />
                                    </template>
                                </el-table-column>
                            </el-table>
                            <!-- 字段分组统计 -->
                            <div class="field-summary">
                                <el-tag v-for="(count, field) in groupExtractions(item.result)" :key="field"
                                        size="small" style="margin: 2px">
                                    {{ getFieldTypeLabel(field) }}: {{ count }}
                                </el-tag>
                            </div>
                        </template>

                        <!-- ===== 文本预处理类型 ===== -->
                        <template v-else-if="item.task_type === 'preprocess'">
                            <div class="preprocess-stats">
                                <el-statistic title="原始长度" :value="item.result.original_length" />
                                <el-statistic title="清洗后长度" :value="item.result.stats?.cleaned_length || 0" />
                                <el-statistic title="总词数" :value="item.result.stats?.total_words || 0" />
                                <el-statistic title="唯一词数" :value="item.result.stats?.unique_words || 0" />
                                <el-statistic title="压缩比" :value="item.result.stats?.reduction_ratio || 0"
                                              suffix="%" />
                                <el-statistic title="纠错条数" :value="item.result.corrections?.length || 0" />
                            </div>
                            <div v-if="item.result.process_logs?.length" class="mini-timeline">
                                <el-tag v-for="(log, i) in item.result.process_logs.filter(l => l.step !== 'init' && l.step !== 'done')"
                                        :key="i" size="small" style="margin: 2px" type="info">
                                    {{ log.name }}
                                </el-tag>
                            </div>
                        </template>

                        <!-- ===== 兜底：原始 JSON ===== -->
                        <template v-else>
                            <pre class="raw-json">{{ JSON.stringify(item.result, null, 2).slice(0, 500) }}</pre>
                        </template>
                    </div>
                </div>
            </div>

            <!-- 分页 -->
            <div class="pagination-wrap" v-if="total > 0">
                <el-pagination
                    background
                    layout="total, sizes, prev, pager, next, jumper"
                    :total="total"
                    v-model:page-size="filterForm.limit"
                    v-model:current-page="filterForm.page"
                    :page-sizes="[10, 20, 50]"
                    @size-change="loadResults"
                    @current-change="loadResults"
                />
            </div>
        </el-card>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { adminRequest } from '@/composables/adminRequest'

const documentList = ref<any[]>([])
const results = ref<any[]>([])
const loading = ref(false)
const total = ref(0)
const layoutMode = ref<'card' | 'compact'>('card')

const filterForm = reactive({
    document_id: null as number | null,
    task_type: '',
    keyword: '',
    page: 1,
    limit: 20,
})

const FIELD_LABELS: Record<string, string> = {
    date: '日期', money: '金额', email: '邮箱', phone: '电话',
    person: '人名', organization: '机构', location: '地点',
}
const FIELD_TAGS: Record<string, string> = {
    date: 'primary', money: 'success', email: 'info', phone: 'warning',
    person: 'danger', organization: '', location: 'success',
}

const getTaskTypeText = (t: string) => ({
    preprocess: '文本预处理', keyword_summary: '关键词摘要', extraction: '信息抽取', batch: '批量处理'
}[t] || t)
const getTaskTypeTag = (t: string) => ({
    preprocess: 'primary', keyword_summary: 'success', extraction: 'warning', batch: 'info'
}[t] || '')
const getFieldTypeLabel = (f: string) => FIELD_LABELS[f] || f
const getFieldTypeTag = (f: string) => FIELD_TAGS[f] || ''

const formatDateTime = (s: string) => s ? new Date(s).toLocaleString('zh-CN') : '-'

const getKwFontSize = (score: number, max: number): number => {
    const ratio = max > 0 ? score / max : 1
    return Math.round(12 + ratio * 8)
}

const getExtractions = (r: any): any[] => {
    if (Array.isArray(r)) return r
    if (Array.isArray(r?.extractions)) return r.extractions
    return []
}
const groupExtractions = (r: any): Record<string, number> => {
    const counts: Record<string, number> = {}
    for (const e of getExtractions(r)) {
        counts[e.field_name] = (counts[e.field_name] || 0) + 1
    }
    return counts
}
const getTopSentences = (r: any, n: number) => {
    const sents = r.summary_all_sentences || []
    const scores = r.summary_sentence_scores || []
    return sents.map((t: string, i: number) => ({ index: i, text: t, score: scores[i] || 0 }))
        .sort((a: any, b: any) => b.score - a.score).slice(0, n)
}
const isSentenceSelected = (r: any, idx: number) =>
    (r.summary_selected_indices || []).includes(idx)

const loadDocuments = async () => {
    try {
        const res: any = await adminRequest.get('/api/document/list?limit=200')
        documentList.value = res?.data?.list || []
    } catch (e) {}
}

const loadResults = async () => {
    loading.value = true
    try {
        const params: any = {
            page: filterForm.page,
            limit: filterForm.limit,
        }
        if (filterForm.document_id) params.document_id = filterForm.document_id
        if (filterForm.task_type) params.task_type = filterForm.task_type
        if (filterForm.keyword) params.keyword = filterForm.keyword
        const res: any = await adminRequest.get('/api/results/all', { params })
        results.value = res?.data?.list || []
        total.value = res?.data?.total || 0
    } catch (e) {
        ElMessage.error('获取结果失败')
    } finally {
        loading.value = false
    }
}

const exportResult = async (taskId: number, format: string) => {
    try {
        const res: any = await adminRequest.get(`/api/task/${taskId}/export?format=${format}`,
            { responseType: 'blob' })
        const blob = new Blob([res])
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        const ext: Record<string, string> = { json: 'json', excel: 'xlsx', csv: 'csv' }
        link.download = `result_${taskId}.${ext[format]}`
        link.click()
        window.URL.revokeObjectURL(url)
        ElMessage.success('导出成功')
    } catch (e) {
        ElMessage.error('导出失败')
    }
}

onMounted(() => {
    loadDocuments()
    loadResults()
})
</script>

<style scoped>
.result-display-container { padding: 20px; }
.main-card { border-radius: 8px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-title { font-size: 18px; font-weight: 600; color: #2c3e50; }
.card-subtitle { font-size: 14px; color: #7f8c8d; }

.filter-bar {
    display: flex; align-items: center; gap: 12px; margin-bottom: 20px;
    padding: 16px; background: #f8f9fa; border-radius: 8px; flex-wrap: wrap;
}

.results-area {
    display: flex; flex-direction: column; gap: 16px; min-height: 200px;
}
.results-area.compact { gap: 8px; }

.result-card {
    background: white; border: 1px solid #e4e7ed; border-radius: 8px;
    overflow: hidden; transition: box-shadow .2s;
}
.result-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,.08); }

.result-card-header {
    display: flex; justify-content: space-between; align-items: center;
    padding: 12px 16px; background: #fafbfc; border-bottom: 1px solid #ebeef5;
}
.header-left { display: flex; align-items: center; gap: 10px; }
.doc-name { font-weight: 600; color: #2c3e50; }
.result-time { font-size: 12px; color: #909399; }
.result-card-body { padding: 16px; }

.section-title {
    font-size: 14px; font-weight: 600; color: #2c3e50;
    margin-bottom: 10px; display: flex; align-items: center; gap: 8px;
}

.kw-section { margin-bottom: 16px; }
.kw-list { display: flex; flex-wrap: wrap; gap: 6px; }
.kw-tag { display: inline-flex; align-items: center; gap: 6px; }
.kw-score { font-size: 10px; opacity: .6; font-family: 'Courier New', monospace; }

.summary-section { padding-top: 12px; border-top: 1px dashed #ebeef5; }
.summary-content {
    background: #f8f9fa; padding: 14px; border-radius: 6px;
    line-height: 1.8; color: #2c3e50; text-indent: 2em; margin: 8px 0;
}
.mini-sentence-list { max-height: 300px; overflow-y: auto; }
.mini-sent {
    padding: 6px 10px; margin: 2px 0; border-radius: 4px;
    font-size: 12px; line-height: 1.6; border-left: 3px solid transparent;
}
.mini-sent.selected { background: #f0f9eb; border-left-color: #67c23a; font-weight: 500; }
.mini-sent strong { color: #409eff; margin-right: 8px; font-family: 'Courier New', monospace; }

.preprocess-stats {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 16px; margin-bottom: 12px;
}
.mini-timeline { padding: 8px 0; }

.field-summary {
    margin-top: 10px; padding-top: 10px; border-top: 1px dashed #ebeef5;
}

.compact .result-card-body { padding: 10px 16px; }
.compact .kw-section, .compact .summary-section { margin-bottom: 8px; }

.raw-json {
    background: #f5f5f5; padding: 10px; border-radius: 4px;
    font-size: 12px; max-height: 200px; overflow: auto;
}

.pagination-wrap {
    margin-top: 20px; display: flex; justify-content: center;
}
</style>
