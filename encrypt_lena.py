# -*- coding: utf-8 -*-
# 对经典测试图（Lena）执行课件里的整条加密链，并验证解密
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
N = 256  # 图像边长（也是灰度模数）
SRC = r"C:\Users\smile\Desktop\2\QQ图片202610101847131.png"


# ---------- 载入 ----------
img = Image.open(SRC).convert("L").resize((N, N), Image.LANCZOS)
A = np.asarray(img, dtype=np.int64)
assert A.shape == (N, N) and A.min() >= 0 and A.max() <= 255

# ---------- 1. 一次一密（矩阵加法 mod 256） ----------
B = np.random.default_rng(9).integers(0, 256, (N, N))          # 密钥 B：随机噪声
C_otp = (A + B) % 256
A_rec = (C_otp - B) % 256
err_otp = int(np.abs(A_rec - A).max())
assert err_otp == 0

# ---------- 2. Arnold 置乱（矩阵乘法搬家，mod 256 坐标） ----------
M = np.array([[2, 1], [1, 1]])
def arnold(mat, rounds):
    out = mat
    idx = np.indices((N, N))
    x, y = idx[1].ravel(), idx[0].ravel()
    for _ in range(rounds):
        x2 = (M[0, 0] * x + M[0, 1] * y) % N
        y2 = (M[1, 0] * x + M[1, 1] * y) % N
        x, y = x2, y2
    out = np.zeros_like(mat)
    out[y, x] = mat.ravel()[(idx[0].ravel() * N + idx[1].ravel())]
    return out

def arnold_inv(mat, rounds):
    # 解密：再走 (周期 - k) 轮；周期 192 已验证（M^192 = E mod 256）
    return arnold(mat, 192 - rounds)

C_arn = arnold(A, 6)
A_rec2 = arnold_inv(C_arn, 6)
err_arn = int(np.abs(A_rec2 - A).max())
assert err_arn == 0, err_arn

# ---------- 3. Hill 块扩散（双边乘 K·A·K，2×2 分块） ----------
K = np.array([[3, 2], [1, 3]])
Kinv = np.array([[37, 146], [73, 37]]) % 256   # det K = 1
print(K @ Kinv % 256)
print(Kinv @ K % 256)
def hill(mat):
    out = np.empty_like(mat)
    for i in range(0, N, 2):
        for j in range(0, N, 2):
            blk = mat[i:i+2, j:j+2]
            out[i:i+2, j:j+2] = (K @ blk @ K) % 256
    return out
def hill_inv(mat):
    out = np.empty_like(mat)
    for i in range(0, N, 2):
        for j in range(0, N, 2):
            blk = mat[i:i+2, j:j+2]
            out[i:i+2, j:j+2] = (Kinv @ blk @ Kinv) % 256
    return out

C_hill = hill(A)
A_rec3 = hill_inv(C_hill)
err_hill = int(np.abs(A_rec3 - A).max())
assert err_hill == 0, err_hill

# ---------- 4. 组合：先置乱，再扩散 ----------
C_mix = hill(C_arn)
A_rec4 = arnold_inv(hill_inv(C_mix), 6)
err_mix = int(np.abs(A_rec4 - A).max())
assert err_mix == 0, err_mix

print("解密误差：一次一密=%d  Arnold置乱=%d  Hill扩散=%d  组合=%d" %
      (err_otp, err_arn, err_hill, err_mix))
print("密文熵(越接近8越随机)：一次一密=%.3f  置乱=%.3f  扩散=%.3f  组合=%.3f" % tuple(
    -(lambda h: sum(v/65536*np.log2(v/65536) for v in h if v))(np.bincount(c.ravel(), minlength=256).astype(float))
    for c in [C_otp, C_arn, C_hill, C_mix]))

# ---------- 出图 ----------
# font_manager.fontManager.addfont(r"  ")
plt.rcParams["font.family"] = "Microsoft YaHei"
plt.rcParams["axes.unicode_minus"] = False

panels = [
    (A,      "原图 A",                 "服务器想保护的对象"),
    (B % 256, "密钥 B（随机噪声）",     "和明文一样大 · 只用一次"),
    (C_otp,  "一次一密密文 C=(A+B) mod 256", "矩阵加法 · 解密误差 = 0"),
    (C_arn,  "Arnold 置乱 6 轮",       "矩阵乘法搬家 · 解密误差 = 0"),
    (C_hill, "Hill 扩散 C=K·A·K（2×2 分块）", "逆矩阵解密 · 解密误差 = 0"),
    (C_mix,  "组合密文：先置乱，再扩散", "工程标准流程 · 解密误差 = 0"),
]
fig, axes = plt.subplots(2, 3, figsize=(13.5, 9.4), dpi=150)
fig.patch.set_facecolor("#F7F5EF")
for ax, (m, title, sub) in zip(axes.ravel(), panels):
    ax.imshow(m, cmap="gray", vmin=0, vmax=255)
    ax.set_title(title, fontsize=13, color="#1a1a18", pad=16)
    ax.text(0.5, 1.005, sub, transform=ax.transAxes, ha="center", va="bottom",
            fontsize=9.5, color="#6b6a63")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color("#c9c7bd")
fig.suptitle("同一张人脸测试图的四种加密 —— 全部由矩阵运算完成，解密误差均为 0",
             fontsize=15, color="#111", y=0.985)
fig.text(0.5, 0.015,
         "测试图：Lena（图像处理标准测试图）· 加解密均在 mod 256 下精确可逆 · 密文统计熵 ≈ 8 bit/像素，无任何可辨认结构",
         ha="center", fontsize=9.5, color="#6b6a63")
fig.tight_layout(rect=[0, 0.03, 1, 0.96], h_pad=2.6)
fig.savefig(r"./image/compare1.png",
            bbox_inches="tight", facecolor=fig.get_facecolor())
print("saved")



MY_SRC = r"C:\Users\smile\Desktop\2\Kirisaki_www_zerochan_net_Beatrice.jpg"          # 改成你的照片路径
my_img = Image.open(MY_SRC).convert("L").resize((N, N), Image.LANCZOS)
Me = np.asarray(my_img, dtype=np.int64)
# 用组合加密（先 Arnold 置乱，再 Hill 扩散）加密我的照片
Me_arn  = arnold(Me, 3)
Me_mix  = hill(Me_arn)
Me_rec  = arnold_inv(hill_inv(Me_mix), 3)   # 解密还原

err_me = int(np.abs(Me_rec - Me).max())
print("我的照片解密误差 =", err_me)

# 三联对比图
fig2, axes2 = plt.subplots(1, 3, figsize=(13, 4.6), dpi=150)
fig2.patch.set_facecolor("#F7F5EF")

panels2 = [
    (Me,     "我本人照片（原图）",   "输入的明文"),
    (Me_mix, "我的照片密文",        "组合加密后的结果"),
    (Me_rec, "解密还原",            "解密误差 = %d" % err_me),
]
for ax, (m, title, sub) in zip(axes2, panels2):
    ax.imshow(m, cmap="gray", vmin=0, vmax=255)
    ax.set_title(title, fontsize=13, pad=12)
    ax.text(0.5, 1.005, sub, transform=ax.transAxes,
            ha="center", va="bottom", fontsize=9.5, color="#6b6a63")
    ax.set_xticks([]); ax.set_yticks([])

fig2.suptitle("【学号+姓名】本人的照片加密实验", fontsize=15, y=0.99)
fig2.tight_layout(rect=[0, 0, 1, 0.94])
fig2.savefig("./image/我的照片加密对比_学号_姓名.png",
             bbox_inches="tight", facecolor=fig2.get_facecolor())
print("已保存：我的照片加密对比_学号_姓名.png")