import os

frontend_path = "frontend/index.html"

with open(frontend_path, "r", encoding="utf-8") as f:
    text = f.read()

# Replace button
text = text.replace('<button class="text-indigo-600 hover:text-indigo-900 font-medium">查看详情 »</button>', 
                    '<button @click="fetchPoiDetail(poi.id)" class="text-indigo-600 hover:text-indigo-900 font-medium cursor-pointer relative z-10">查看详情 »</button>')

modal = """
        <!-- 弹窗 -->
        <div v-if="selectedPoi" class="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" @click="closeModal" aria-hidden="true"></div>
                <span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
                <div class="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
                    <div class="sm:flex sm:items-start">
                        <div class="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-indigo-100 sm:mx-0 sm:h-10 sm:w-10">
                            <span class="text-indigo-600 text-xl font-bold">#</span>
                        </div>
                        <div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                            <h3 class="text-lg leading-6 font-medium text-gray-900" id="modal-title">
                                {{ selectedPoi.name }}
                            </h3>
                            <div class="mt-2 text-sm text-gray-500">
                                <p class="mb-1"><span class="font-semibold text-gray-700">分类:</span> {{ selectedPoi.category }}</p>
                                <p class="mb-1" v-if="selectedPoi.city"><span class="font-semibold text-gray-700">城市:</span> {{ selectedPoi.city }}</p>
                                <p class="mb-1"><span class="font-semibold text-gray-700">位置坐标:</span> [{{ selectedPoi.latitude }}, {{ selectedPoi.longitude }}]</p>
                                <p class="mt-2 whitespace-pre-line leading-relaxed"><span class="font-semibold text-gray-700">描述信息:<br></span>{{ selectedPoi.description || '暂无详细描述，这是一个很棒的景点。' }}</p>
                            </div>
                        </div>
                    </div>
                    <div class="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
                        <button type="button" @click="closeModal" class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm">
                            关闭面板
                        </button>
                    </div>
                </div>
            </div>
        </div>
"""

# Insert modal before `<!-- 空数据提示 -->`
if "<!-- 弹窗 -->" not in text:
    text = text.replace('<!-- 空数据提示 -->', modal + '\n        <!-- 空数据提示 -->')

js_add = """
                const selectedPoi = ref(null);

                const fetchPoiDetail = async (id) => {
                    loading.value = true;
                    try {
                        const response = await axios.get(`http://localhost:8000/api/recommendation/suggest/attractions/${id}`);
                        if (response.data && response.data.data) {
                            selectedPoi.value = response.data.data;
                        } else {
                            alert("获取详情失败，内容为空！");
                        }
                    } catch (err) {
                        console.error('获取详情失败:', err);
                        alert(err.message || '未知网络错误');
                    } finally {
                        loading.value = false;
                    }
                };

                const closeModal = () => {
                    selectedPoi.value = null;
                };
"""

if "const selectedPoi = ref(null);" not in text:
    text = text.replace('const limit = ref(12);', 'const limit = ref(12);' + js_add)

ret_str = """
                return {
                    attractions,
                    loading,
                    error,
                    sortBy,
                    limit,
                    selectedPoi,
                    fetchPoiDetail,
                    closeModal,
"""
if "selectedPoi," not in text:
    text = text.replace('return {\n                    attractions,', ret_str)

with open(frontend_path, "w", encoding="utf-8") as f:
    f.write(text)

