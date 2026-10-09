WITH phongban_tree (mapb, tenpb, mapb_cha, cap) AS (
    SELECT mapb, tenpb, mapb_cha, 1
    FROM phongban
    WHERE mapb_cha IS NULL

    UNION ALL

    SELECT pb.mapb, pb.tenpb, pb.mapb_cha, pbt.cap + 1
    FROM phongban pb
    JOIN phongban_tree pbt ON pb.mapb_cha = pbt.mapb
)
SELECT 
    LPAD(' ', (cap - 1) * 4) || tenpb AS cay_phong_ban,
    mapb,
    mapb_cha,
    cap
FROM phongban_tree;
