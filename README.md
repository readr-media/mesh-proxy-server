# mesh-proxy-server
### 目的
為Mesh的反向代理伺服器(Reverse-proxy server)，用來快取資料、減少資料庫連線數量，並且隱藏後台伺服器的資訊。
在建立好伺服器之後，可以進入到/doc的路由查看Fastapi提供的APIs手冊。

### 使用方式
進入到/doc路由查看APIs手冊如下，其中root路由用於Health-checking，而gql路由用來快取GQL請求。
![image](https://github.com/readr-media/mesh-proxy-server/assets/34787189/0682ee34-3a8d-404d-a8e0-a7b9e1d1ede9)
點開/gql，可以發現到這個API需要application/json的Request body
![image](https://github.com/readr-media/mesh-proxy-server/assets/34787189/adf04813-083d-4723-9e60-6cc48a04730d)
其中三個欄位分別解釋如下
* query: GQL query
* (Optional) variable: GQL variable
* (Optional) ttl: time-to-live, 為快取在Proxy伺服器中的存活時間

### 架構圖
![mesh-architecture](https://github.com/readr-media/mesh-proxy-server/assets/34787189/70335a4e-268f-4206-a141-4d5aca6af458)
在Reverser-proxy當中串接的對象有幾個:
1. Pub/sub: 寫入pick(選擇媒體)、like(使用者喜歡的文章)、comment(使用者評論)導到後台Pub/sub去做處理。
2. GQL: 針對GQL請求，我們會以cache_key=MD5(Request)到Redis進行快取查詢。若資料存在則回傳，不存在則導到GQL伺服器抓取資料並寫入快取。

### 本地建置
請先下載Docker desktop並確保為開啟狀態，並在MESH-PROXY-SERVER的主資料夾底下輸入以下指令:
1. 新增.env: 設定環境變數
2. 啟動專案: docker compose up -d --build
3. 關閉專案: docker compose down
4. (Optional)清除資源: docker system prune

接下來我們要講解Redis的debug流程，在開始前請先確保伺服器有正確啟動:
1. 新開Terminal
2. 連線至Redis: docker exec -it redis-cache sh
3. 啟動Redis-cli: redis-cli
4. 查詢keys: keys *
