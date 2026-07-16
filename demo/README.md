# BLACKBOX Case Files Demo

這是一個 React 單頁式 MongoDB 資料瀏覽器，畫面採用黑客終端機與特務案件檔案風格。前端和 API 都放在 `demo` 資料夾內，不需要修改 crawler。

## 環境需求

- Node.js 18 以上
- 專案根目錄的 `.env` 必須包含：

```env
MONGO_URL=你的 MongoDB 連線字串
MONGO_DB=你的資料庫名稱
```

API 預設讀取 MongoDB 的 `posts` collection。

## 第一次安裝

在 `demo` 資料夾執行：

```powershell
npm install
```

## 啟動方式

請開啟兩個終端機，兩邊都先進入 `demo` 資料夾。

終端機 1，啟動 MongoDB API：

```powershell
npm run api
```

終端機 2，啟動 React 前端：

```powershell
npm run dev
```

接著開啟：

```text
http://127.0.0.1:5173
```

- React 前端：`http://127.0.0.1:5173`
- MongoDB API：`http://127.0.0.1:4141`
- API 健康檢查：`http://127.0.0.1:4141/api/health`

如果 `5173` 已被占用，Vite 會自動使用 `5174`、`5175` 等其他連接埠。前端透過內建 `/api` proxy 連線，因此不需要另外修改 API 網址。

## 使用方式

- `TRACE QUERY` 可以搜尋作者、內容或社團名稱。
- `CASE INDEX` 顯示 MongoDB 中的貼文列表。
- 點選案件後，右側會顯示內容、日期、來源社團與原始網址。
- `OPEN SOURCE URL` 開啟原始貼文。
- `OPEN GROUP` 開啟來源社團。

## Windows 出現 spawn EPERM

專案已在 `vite.config.js` 啟用 `preserveSymlinks`，並透過 `scripts/vite-windows.mjs` 啟動開發伺服器，避免 Vite 在 Windows 解析路徑時執行被系統封鎖的 `net use`。

如果瀏覽器仍停在舊的錯誤畫面：

1. 在前端終端機按 `Ctrl+C` 停止舊程序。
2. 重新執行 `npm run dev`。
3. 在瀏覽器按 `Ctrl+Shift+R` 強制重新整理。

## 畫面顯示 CONNECTION FAILED

請確認：

- `npm run api` 與 `npm run dev` 都正在執行。
- 根目錄 `.env` 有正確的 `MONGO_URL` 與 `MONGO_DB`。
- MongoDB 可連線，而且 `posts` collection 內有資料。

如果錯誤包含 `querySrv ECONNREFUSED`，代表 DNS 無法查詢 MongoDB Atlas 的 SRV 記錄。Demo API 會自動嘗試 `1.1.1.1` 與 `8.8.8.8`；也可以在根目錄 `.env` 使用 `DEMO_DNS_SERVERS=你的DNS1,你的DNS2` 覆寫，或在 MongoDB Atlas 的 Connect 畫面取得不使用 `mongodb+srv://` 的 Standard connection string。

可直接測試 API：

```text
GET http://127.0.0.1:4141/api/posts?limit=180
GET http://127.0.0.1:4141/api/posts?search=台北
```
