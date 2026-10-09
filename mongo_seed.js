// Chay trong MongoDB Compass Shell hoac mongosh.
// Database: hrm_pro_db
// Trong Compass Shell nen dung db.getSiblingDB thay cho lenh use.

db = db.getSiblingDB("hrm_pro_db");

db.leave_requests.deleteMany({});
db.overtime_requests.deleteMany({});
db.performance_reviews.deleteMany({});

db.leave_requests.insertMany([
  {
    ma_don: "NP001",
    ma_nv: "NV001",
    loai_don: "NGHI_PHEP",
    tu_ngay: "2026-06-01",
    den_ngay: "2026-06-03",
    so_ngay: 3,
    ly_do: "Viec gia dinh",
    trang_thai: "CHO_DUYET",
    sync_status: "PENDING",
    error_message: "",
    created_at: new Date(),
    updated_at: new Date(),
    lich_su_duyet: []
  },
  {
    ma_don: "NP002",
    ma_nv: "NV002",
    loai_don: "NGHI_PHEP",
    tu_ngay: "2026-06-05",
    den_ngay: "2026-06-05",
    so_ngay: 1,
    ly_do: "Kham benh",
    trang_thai: "DA_DUYET",
    sync_status: "SUCCESS",
    error_message: "",
    created_at: new Date(),
    updated_at: new Date(),
    lich_su_duyet: []
  },
  {
    ma_don: "NP003",
    ma_nv: "NV003",
    loai_don: "NGHI_PHEP",
    tu_ngay: "2026-06-10",
    den_ngay: "2026-06-11",
    so_ngay: 2,
    ly_do: "Viec ca nhan",
    trang_thai: "TU_CHOI",
    sync_status: "SUCCESS",
    error_message: "",
    created_at: new Date(),
    updated_at: new Date(),
    lich_su_duyet: []
  }
]);

db.overtime_requests.insertOne({
  ma_don: "OT001",
  ma_nv: "NV005",
  ngay_lam_them: "2026-06-07",
  so_gio: 3,
  ly_do: "Hoan thanh module backend",
  trang_thai: "CHO_DUYET",
  created_at: new Date()
});

db.performance_reviews.insertMany([
  {
    ma_danh_gia: "DG001",
    ma_nv: "NV001",
    quy: "Q2",
    nam: 2026,
    diem: 8.5,
    nhan_xet_quan_ly: "Hoan thanh tot cong viec, co kha nang ho tro nhom.",
    nhan_xet_nhan_vien: "Can cai thien ky nang lap ke hoach."
  },
  {
    ma_danh_gia: "DG002",
    ma_nv: "NV002",
    quy: "Q2",
    nam: 2026,
    diem: 7.8,
    nhan_xet_quan_ly: "Tien do on dinh, can chu dong hon khi xu ly loi.",
    nhan_xet_nhan_vien: "Muon duoc tham gia them du an thuc te."
  }
]);

db.leave_requests.aggregate([
  {
    $group: {
      _id: "$trang_thai",
      so_luong: { $sum: 1 }
    }
  },
  {
    $sort: {
      so_luong: -1
    }
  }
]);
