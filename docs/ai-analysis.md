# Chatbot AI cho livestream

## Muc tieu

Chatbot tu dong tra loi cac cau hoi pho bien cua khach trong phien livestream ban hang.

## API

```text
POST /chatbot/reply
```

Payload:

- `message`: tin nhan moi nhat cua khach.
- `customer_name`: ten khach neu co.
- `account_name`: ten phong live.
- `products`: danh sach san pham trong live.
- `conversation_history`: lich su chat gan nhat.

Response:

```json
{
  "reply": "Da An, Serum Vitamin C dang co gia live 129.000 d...",
  "intent": "ask_price",
  "sentiment": "neutral",
  "confidence": 0.86,
  "should_escalate": false,
  "suggested_actions": ["Gui gia live va hoi so luong khach muon chot."],
  "used_product_id": "product-01"
}
```

## Nhom cau hoi chatbot xu ly

- Hoi gia live hoac uu dai.
- Hoi ton kho.
- Hoi phi ship hoac khu vuc giao hang.
- Muon mua hoac chot don.
- Can tu van san pham.
- Khieu nai hoac muon gap nhan vien.

## Handoff

Khi khach yeu cau gap nhan vien hoac co phan hoi tieu cuc, chatbot tra loi lich su va dat `should_escalate = true` de app co the hien thi can nhan vien tiep quan.
