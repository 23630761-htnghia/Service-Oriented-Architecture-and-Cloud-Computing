# Triển khai Databricks

Phần Databricks đã được tách khỏi repo này.

Lý do:

- Nhóm sẽ thao tác trực tiếp trên Databricks Workspace.
- Môi trường hiện tại không có cluster/compute phù hợp để duy trì artefact Databricks ngay trong repo.
- Việc giữ notebook, job template và script submit trong repo dễ gây nhầm rằng dự án cần cấu hình Databricks cục bộ để demo.

Phạm vi hiện tại của repo:

- Giữ lại app demo khách hàng và người bán.
- Giữ lại backend AI để phân tích comment và hỗ trợ trả lời comment có ý định mua.
- Không còn lưu notebook, job JSON, submit template hay sample data dành riêng cho Databricks trong mã nguồn này.

Khi cần viết báo cáo hoặc demo cloud:

- Thực hiện trực tiếp trên Databricks Workspace của nhóm.
- Lưu ảnh chụp workspace, cluster/compute, notebook, job run và bảng dữ liệu từ môi trường Databricks thật.
- Tài liệu hoặc minh chứng Databricks nên quản lý riêng ngoài repo ứng dụng này.
