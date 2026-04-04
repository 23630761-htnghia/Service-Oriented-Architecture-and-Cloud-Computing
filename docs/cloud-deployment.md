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

## 3.3. Tiến độ triển khai trên Databricks

Tiến độ triển khai trên Databricks được trình bày theo các nội dung sau:

1. Workspace/Cluster đã thiết lập  
   Nhóm đã tạo Databricks Workspace và cấu hình cluster hoặc compute phục vụ cho quá trình chạy notebook, xử lý dữ liệu và demo hệ thống.

2. Notebook/Jobs đã tạo  
   Các notebook xử lý dữ liệu và Databricks Jobs đã được khởi tạo để phục vụ việc chạy thử nghiệm, tự động hóa một số bước xử lý và theo dõi kết quả thực thi.

3. Data ingestion/ETL đã thực hiện  
   Nhóm đã đưa dữ liệu vào Databricks và tiến hành các bước ETL cơ bản gồm nạp dữ liệu, làm sạch, chuyển đổi và kiểm tra kết quả trước khi đưa vào xử lý tiếp theo.

4. Delta Lake hoặc pipeline đã thử nghiệm  
   Nhóm đã thử nghiệm lưu trữ hoặc xử lý dữ liệu bằng Delta Lake, hoặc đã chạy pipeline trên Databricks để kiểm chứng khả năng vận hành của hệ thống trong môi trường cloud.

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
