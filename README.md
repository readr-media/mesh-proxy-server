# mesh-proxy-server
### 目的
為Mesh的反向代理伺服器(Reverse-proxy server)，用來快取資料、減少資料庫連線數量，並且隱藏後台伺服器的資訊。
在建立好伺服器之後，可以進入到/doc的路由查看Fastapi提供的APIs手冊。

### 架構圖
![mesh-architecture](https://github.com/readr-media/mesh-proxy-server/assets/34787189/32e2a2a4-8f87-45aa-9dd3-833e0cc037bf)
在Reverser-proxy當中串接的對象有幾個:
1. Pub/sub: 寫入pick(選擇媒體)、like(使用者喜歡的文章)、comment(使用者評論)導到後台Pub/sub去做處理。
2. GQL: 我們會在共用同一連線下轉送gql query到GQL伺服器取得資料，並對Queries進行快取。
3. Redis: Redis裡會放各家媒體最新的文章，在部分情境下我們會直接向Redis取得文章。

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