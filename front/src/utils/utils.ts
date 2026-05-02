export const getAdminList = () => {
	const routes = [
		{
			"path": "/",
			"name": "首页",
			"icon": "House"
		},
		{
			"path": "/document-import",
			"name": "文档导入",
			"icon": "Upload"
		},
		{
			"path": "/text-preprocess",
			"name": "文本预处理",
			"icon": "Edit"
		},
		{
			"path": "/information-extraction",
			"name": "信息抽取",
			"icon": "Search"
		},
		{
			"path": "/keyword-summary",
			"name": "关键词摘要",
			"icon": "Key"
		},
		{
			"path": "/result-display",
			"name": "结果导出",
			"icon": "DataLine"
		},
		{
			"path": "/batch-processing",
			"name": "批量处理",
			"icon": "Operation"
		}
	]
	return routes;
}
