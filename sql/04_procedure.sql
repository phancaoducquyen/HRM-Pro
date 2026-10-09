CREATE OR REPLACE PROCEDURE SP_TRU_NGAY_PHEP (
    p_manv IN VARCHAR2,
    p_ma_don IN VARCHAR2,
    p_so_ngay IN NUMBER
)
AS
    v_ngayphep_conlai NUMBER;
BEGIN
    SELECT NGAYPHEP_CONLAI
    INTO v_ngayphep_conlai
    FROM NHANVIEN
    WHERE MANV = p_manv;

    IF v_ngayphep_conlai < p_so_ngay THEN
        RAISE_APPLICATION_ERROR(-20001, 'Nhan vien khong du ngay phep');
    END IF;

    UPDATE NHANVIEN
    SET NGAYPHEP_CONLAI = NGAYPHEP_CONLAI - p_so_ngay
    WHERE MANV = p_manv;

    INSERT INTO LICHSU_PHEP (
        MALICHSU, MANV, MA_DON, SO_NGAY_TRU, NGAY_XULY, GHICHU
    )
    VALUES (
        'LS' || TO_CHAR(SYSDATE, 'YYYYMMDDHH24MISS'),
        p_manv,
        p_ma_don,
        p_so_ngay,
        SYSDATE,
        'Tru ngay phep do don nghi phep da duyet'
    );

    COMMIT;
END;
/
