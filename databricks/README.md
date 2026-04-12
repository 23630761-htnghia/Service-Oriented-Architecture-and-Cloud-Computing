# Databricks Workflow

## 1. Mục đích

Thư mục này chứa phần mở rộng của đồ án để phục vụ triển khai và báo cáo tiến độ trên Databricks. Luồng hiện tại bám đúng bài đang có trong repo:

- lấy dữ liệu comment đã sync từ hệ thống local,
- ingest lên Databricks,
- xử lý ETL theo pipeline bronze -> silver -> gold,
- lưu dữ liệu bằng Delta Lake,
- chạy bằng Databricks Job hoặc submit online qua Jobs REST API.

## 2. Công nghệ sử dụng trong phần Databricks

### Ngôn ngữ và công cụ

- Python `3.11` cho phần local/Docker của dự án
- Python / PySpark cho notebook ETL
- PowerShell cho script submit online
- JSON cho job template và submit payload
- Delta Lake cho lưu trữ bảng bronze, silver, gold

### Yêu cầu môi trường

- Databricks Workspace
- một cluster hoặc compute đang chạy
- Databricks Runtime có hỗ trợ Python / PySpark
- notebook đã import vào Workspace
- `DATABRICKS_HOST`
- `DATABRICKS_TOKEN`
- `existing_cluster_id` nếu chạy theo hướng submit online

## 3. Các file chính

- `notebooks/01_ingest_sync_records.py`
  Nạp dữ liệu JSON vào bảng Delta bronze.
- `notebooks/02_transform_to_silver.py`
  Làm sạch dữ liệu, flatten cột `analysis`, deduplicate và `repartition` để xử lý song song.
- `notebooks/03_build_gold_metrics.py`
  Tổng hợp KPI theo ngày và nền tảng vào bảng Delta gold.
- `jobs/smartlive_comment_pipeline.job.json`
  Template Databricks Job nhiều task.
- `submits/smartlive_comment_pipeline.submit.template.json`
  Template payload cho `jobs/runs/submit`.
- `scripts/submit_and_track_run.ps1`
  Script submit online, poll trạng thái và ghi summary ra file.
- `sample_data/sync_records_sample.json`
  Dữ liệu mẫu để demo nhanh.

## 4. Dữ liệu đầu vào cho bài hiện tại

Có 2 cách lấy dữ liệu:

### Cách 1: dùng dữ liệu thật từ hệ thống local

Sau khi chạy backend và tạo vài lượt sync comment:

```bash
curl http://localhost:8000/api/v1/sync/records/export > sync_records_export.json
```

File export này là đầu vào phù hợp nhất với bài hiện tại vì dữ liệu được lấy trực tiếp từ `sync-service`.

### Cách 2: dùng dữ liệu mẫu

Nếu chưa có dữ liệu sync thật, dùng:

- `sample_data/sync_records_sample.json`

## 5. Các bước chung để demo trên Databricks

1. Tạo folder trong Workspace, ví dụ `/Shared/smartlive-databricks`.
2. Tạo cluster hoặc compute để chạy notebook.
3. Upload file JSON đầu vào lên DBFS, ví dụ:
   - `dbfs:/FileStore/smartlive/raw/sync_records_sample.json`
4. Import 3 notebook vào Workspace:
   - `01_ingest_sync_records`
   - `02_transform_to_silver`
   - `03_build_gold_metrics`
5. Chạy pipeline theo một trong hai cách:
   - chạy bằng Databricks Job,
   - hoặc submit online qua script.
6. Kiểm tra bảng kết quả:
   - `main.default.smartlive_sync_comments_bronze`
   - `main.default.smartlive_sync_comments_silver`
   - `main.default.smartlive_daily_metrics_gold`

## 6. Chạy bằng Databricks Job

Nếu muốn trình bày theo hướng có job cố định trong UI:

1. Import file `jobs/smartlive_comment_pipeline.job.json`.
2. Thay `existing_cluster_id` bằng cluster thật.
3. Run job trong giao diện Databricks.
4. Chụp:
   - danh sách task,
   - lịch sử run,
   - trạng thái thành công,
   - output của từng task.

## 7. Chạy online bằng submit

### Thiết lập biến môi trường

```powershell
$env:DATABRICKS_HOST = ""
$env:DATABRICKS_TOKEN = ""
```

### Submit pipeline

```powershell
.\databricks\scripts\submit_and_track_run.ps1 `
  -ExistingClusterId "<existing-cluster-id>" `
  -JobsApiVersion "2.0" `
  -NotebookBasePath "/Shared/smartlive-databricks" `
  -InputPath "dbfs:/FileStore/smartlive/raw/sync_records_sample.json"
```

### Theo dõi lại một run đã có

```powershell
.\databricks\scripts\submit_and_track_run.ps1 -RunId "<run-id>"
```

### Kết quả script tạo ra

Script sẽ:

- gọi `jobs/runs/submit`,
- poll `jobs/runs/get`,
- lấy notebook output của từng task,
- lưu kết quả tại `databricks/runs/`.

Các file quan trọng:

- `databricks/runs/latest-submit-response.json`
- `databricks/runs/latest-run-status.json`
- `databricks/runs/latest-run-summary.md`

## 8. Điểm phù hợp với bài hiện tại

- Dữ liệu đầu vào lấy từ `sync-service` nên bám sát đúng luồng comment analysis của bài.
- Notebook silver có `repartition` theo `platform` và `event_date`, phù hợp để trình bày xử lý song song trên cluster Databricks.
- Notebook gold tạo bảng KPI trực tiếp từ dữ liệu đã enrich, phù hợp để minh họa phần báo cáo tiến độ triển khai cloud.
- Mỗi notebook đều trả về summary qua `dbutils.notebook.exit()`, nên có thể theo dõi output từng task khi submit online.

## 9. Minh chứng nên chụp cho báo cáo tiến độ

### 1. Workspace/Cluster đã thiết lập

- folder trong Workspace,
- cluster hoặc compute ở trạng thái running.

### 2. Notebook/Jobs đã tạo

- 3 notebook đã import,
- job hoặc run online đã tạo thành công.

### 3. Data ingestion/ETL đã thực hiện

- màn hình notebook bronze hoặc silver chạy thành công,
- dữ liệu đầu vào đã upload lên DBFS.

### 4. Delta Lake hoặc pipeline đã thử nghiệm

- bảng bronze, silver, gold trong Catalog Explorer,
- kết quả job run hoặc submit run hoàn tất.

### 5. Submit run online

- `run_id`,
- `run_page_url`,
- file `latest-run-summary.md`.

## 10. Ghi chú

- Mặc định script để `JobsApiVersion = 2.0` vì payload `runs/submit` hiện đang tương thích tốt với luồng multi-task đã chuẩn bị.
- Nếu workspace của bạn dùng Jobs API `2.1` hoặc `2.2`, có thể đổi bằng tham số `-JobsApiVersion`.
- Thư mục `databricks/runs/` chỉ dùng để chứa output sinh ra sau khi submit, không phải dữ liệu nguồn của dự án.
