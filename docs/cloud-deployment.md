# Tích hợp cloud trên Databricks

## 1. Yêu cầu nền tảng triển khai

Nền tảng cloud sử dụng cho đồ án là `Databricks`.

Báo cáo không trình bày theo hướng đề xuất nhiều nhà cung cấp cloud như AWS, Azure hay Render. Toàn bộ nội dung triển khai cần tập trung vào cách nhóm cấu hình, vận hành và demo hệ thống trên Databricks.

## 2. Mục tiêu triển khai trên Databricks

Hệ thống thể hiện được các nội dung sau trên Databricks:

- Quản lý workspace phục vụ phát triển và demo.
- Tạo cluster hoặc compute phù hợp cho việc chạy notebook, job và xử lý dữ liệu.
- Lưu trữ dữ liệu tập trung phục vụ pipeline và phân tích.
- Theo dõi quá trình thực thi job, log và kết quả xử lý.
- Hỗ trợ demo hệ thống online bằng các tài nguyên đã được tạo trên Databricks.

## 3. Phương án triển khai bắt buộc

Phương án triển khai của nhóm được xác định như sau:

- Nền tảng cloud: `Databricks`.
- Môi trường làm việc: Databricks Workspace.
- Xử lý và điều phối tác vụ: Databricks Notebook và Databricks Jobs.
- Lưu trữ dữ liệu: Databricks File System (DBFS) hoặc volume/bảng dữ liệu trong workspace.
- Giám sát: giao diện theo dõi job run, cluster, log và lịch sử thực thi trên Databricks.

## 3.1. Artefact đã chuẩn bị trong repo

Nhóm đã bổ sung sẵn các artefact phục vụ triển khai Databricks ngay trong repo:

- `databricks/notebooks/01_ingest_sync_records.py`: ingest dữ liệu comment sync vào bảng Delta bronze.
- `databricks/notebooks/02_transform_to_silver.py`: ETL, flatten dữ liệu và repartition để xử lý song song trên cluster.
- `databricks/notebooks/03_build_gold_metrics.py`: tổng hợp KPI theo ngày và nền tảng vào bảng Delta gold.
- `databricks/jobs/smartlive_comment_pipeline.job.json`: template Databricks Job gồm 3 task.
- `databricks/submits/smartlive_comment_pipeline.submit.template.json`: template payload cho Databricks `jobs/runs/submit`.
- `databricks/scripts/submit_and_track_run.ps1`: script submit online, theo dõi tiến độ và lưu summary ra file.
- `databricks/sample_data/sync_records_sample.json`: dữ liệu mẫu để upload lên DBFS và chạy thử ngay.
- `GET /api/v1/sync/records/export`: API export dữ liệu đã sync từ hệ thống hiện tại sang JSON để đưa vào Databricks.

Nhờ đó, phần triển khai trên Databricks không chỉ dừng ở mức mô tả kiến trúc mà đã có notebook, job và dữ liệu đầu vào cụ thể để chạy demo.

## 3.3. Tiến độ triển khai trên Databricks

Tiến độ triển khai trên Databricks được trình bày theo các nội dung sau:

1. Workspace/Cluster đã thiết lập  
   Nhóm đã tạo Databricks Workspace và cấu hình cluster hoặc compute phục vụ cho quá trình chạy notebook, xử lý dữ liệu và demo hệ thống.  
   Minh chứng nên đính kèm:
   - Workspace folder `/Shared/smartlive-databricks`.
   - Cluster hoặc compute đang ở trạng thái `Running`.

2. Notebook/Jobs đã tạo  
   Các notebook xử lý dữ liệu và Databricks Jobs đã được khởi tạo để phục vụ việc chạy thử nghiệm, tự động hóa một số bước xử lý và theo dõi kết quả thực thi. Trong repo hiện có sẵn:
   - `01_ingest_sync_records`
   - `02_transform_to_silver`
   - `03_build_gold_metrics`
   - Job template `smartlive-comment-delta-pipeline`
   - Submit template `smartlive_comment_pipeline.submit.template.json`
   Minh chứng nên đính kèm:
   - ảnh import notebook vào Workspace,
   - ảnh cấu hình Job nhiều task,
   - ảnh lịch sử run của Job hoặc run online sau khi submit.

3. Data ingestion/ETL đã thực hiện  
   Nhóm đã đưa dữ liệu vào Databricks và tiến hành các bước ETL cơ bản gồm nạp dữ liệu, làm sạch, chuyển đổi và kiểm tra kết quả trước khi đưa vào xử lý tiếp theo.  
   Luồng đề xuất cho demo:
   - export dữ liệu từ gateway qua `GET /api/v1/sync/records/export`, hoặc dùng `databricks/sample_data/sync_records_sample.json`,
   - upload file JSON lên `dbfs:/FileStore/smartlive/raw/`,
   - chạy notebook `01_ingest_sync_records` để tạo bảng bronze,
   - chạy notebook `02_transform_to_silver` để làm sạch, flatten và repartition.
   Minh chứng nên đính kèm:
   - file JSON đã upload trên DBFS,
   - kết quả hiển thị bảng bronze hoặc silver sau ETL.

4. Delta Lake hoặc pipeline đã thử nghiệm  
   Nhóm đã thử nghiệm lưu trữ hoặc xử lý dữ liệu bằng Delta Lake, hoặc đã chạy pipeline trên Databricks để kiểm chứng khả năng vận hành của hệ thống trong môi trường cloud.  
   Trong repo, notebook `03_build_gold_metrics` ghi dữ liệu tổng hợp vào bảng Delta `main.default.smartlive_daily_metrics_gold`, còn cả Job template và submit template đều chạy đủ chuỗi bronze -> silver -> gold.  
   Minh chứng nên đính kèm:
   - Catalog Explorer hiển thị các bảng Delta,
   - giao diện Job run hoàn tất 3 task,
   - hoặc `run_page_url` và file summary sau khi submit online,
   - kết quả truy vấn bảng gold phục vụ báo cáo KPI.

Mỗi mục tiến độ cần đi kèm minh chứng cụ thể như ảnh chụp workspace, cluster, notebook, job run, bảng dữ liệu hoặc kết quả pipeline trên Databricks.

## 5. Minh chứng bắt buộc trên Databricks

Báo cáo cần đính kèm minh chứng thực tế từ Databricks, ưu tiên các hình ảnh hoặc ảnh chụp màn hình sau:

- Giao diện Databricks Workspace của nhóm.
- Cluster hoặc compute đã được tạo và trạng thái hoạt động.
- Notebook, job hoặc pipeline đã được upload/cấu hình.
- Lịch sử chạy job, kết quả run thành công hoặc thất bại.
- Bảng dữ liệu, tệp dữ liệu hoặc kết quả xử lý trong Databricks.
- Log, dashboard theo dõi hoặc màn hình thể hiện quá trình thực thi.

Không chỉ mô tả lý thuyết. Báo cáo cần có minh chứng cụ thể để xác nhận nhóm đã triển khai trên Databricks.

## 6. Cách viết phần báo cáo cho đúng yêu cầu

Khi viết báo cáo, nhóm nên trình bày theo cấu trúc:

- Yêu cầu nền tảng: sử dụng Databricks.
- Kiến trúc triển khai trên Databricks.
- Các bước đã thực hiện theo tiến độ.
- Minh chứng ảnh chụp màn hình trên Databricks.
- Đánh giá kết quả triển khai và các hạn chế còn tồn tại.

Với yêu cầu này, phần cloud deployment trong báo cáo cần được chỉnh sửa theo hướng `đã triển khai trên Databricks như thế nào` thay vì `có thể triển khai trên cloud nào`.

## 7. Câu mô tả ngắn có thể đưa thẳng vào báo cáo

Có thể viết ngắn gọn phần tiến độ như sau:

`Nhóm đã bổ sung pipeline xử lý song song trên Databricks bằng 3 notebook gồm ingest, ETL và tổng hợp KPI. Dữ liệu comment sau khi export từ sync-service được upload lên DBFS, chạy qua pipeline bronze -> silver -> gold và lưu bằng Delta Lake. Đồng thời, Databricks Job nhiều task đã được cấu hình để tự động hóa toàn bộ luồng và theo dõi tiến trình thực thi trên cluster.`

Nếu cần nhấn mạnh hình thức submit online, có thể dùng câu:

`Ngoài cấu hình Job trên giao diện Databricks, nhóm còn chuẩn bị payload va script submit online qua Jobs REST API. Khi submit, hệ thống trả về run_id, run_page_url va trạng thái từng task, nhờ đó nhóm có thể theo dõi tiến độ thực thi và lưu minh chứng trực tiếp cho phần báo cáo cloud deployment.`
