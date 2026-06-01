import io
import streamlit as st
from PIL import Image

STAMP_W, STAMP_H = 320, 270
TAB_W, TAB_H = 96, 74
MAX_FRAMES = 8
MAX_KB = 300

st.set_page_config(page_title="LINEアニメスタンプメーカー", page_icon="🎬", layout="centered")
st.title("🎬 LINEアニメーションスタンプメーカー")
st.caption("自分で用意した絵をアップロードするだけで、LINE申請用のAPNGが作れます。")

# ── 画像アップロード ────────────────────────────────────────────
st.markdown("### 1. 画像をアップロード")
st.info(f"PNG / JPG を最大{MAX_FRAMES}枚まで。アップロードした順がアニメーションの順番になります。")

uploaded = st.file_uploader(
    "画像を選択（複数可）",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True,
)

if not uploaded:
    st.stop()

if len(uploaded) > MAX_FRAMES:
    st.error(f"画像は{MAX_FRAMES}枚以内にしてください。（現在{len(uploaded)}枚）")
    st.stop()

# ── フレーム読み込み＆プレビュー ───────────────────────────────
frames_raw: list[Image.Image] = []
for f in uploaded:
    img = Image.open(f).convert("RGBA")
    frames_raw.append(img)

st.markdown("### 2. フレーム確認")
cols = st.columns(min(len(frames_raw), 4))
for i, img in enumerate(frames_raw):
    with cols[i % 4]:
        st.image(img, caption=f"フレーム {i+1}", use_container_width=True)

# ── 設定 ──────────────────────────────────────────────────────
st.markdown("### 3. 設定")

col1, col2 = st.columns(2)
with col1:
    duration_ms = st.slider(
        "1フレームの表示時間（ミリ秒）",
        min_value=50,
        max_value=500,
        value=150,
        step=10,
        help="小さいほど速いアニメーションになります"
    )
with col2:
    fit_mode = st.radio(
        "リサイズ方法",
        ["余白を入れて収める（letterbox）", "トリミングして埋める（crop）"],
        help="320×270に合わせる方法を選択"
    )
    use_crop = fit_mode.startswith("トリミング")

use_transparent = st.checkbox("余白を透明にする", value=False)
if not use_transparent:
    bg_color_hex = st.color_picker("余白の背景色（letterboxのとき）", "#FFFFFF")
    bg_rgb = tuple(int(bg_color_hex[i:i+2], 16) for i in (1, 3, 5))
    bg_color = bg_rgb + (255,)
else:
    bg_color = (0, 0, 0, 0)


def resize_frame(img: Image.Image) -> Image.Image:
    """320×270にリサイズ。cropモードはトリミング、letterboxは余白追加。"""
    src_w, src_h = img.size
    target_ratio = STAMP_W / STAMP_H
    src_ratio = src_w / src_h

    if use_crop:
        if src_ratio > target_ratio:
            new_h = STAMP_H
            new_w = int(src_ratio * new_h)
        else:
            new_w = STAMP_W
            new_h = int(new_w / src_ratio)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - STAMP_W) // 2
        top = (new_h - STAMP_H) // 2
        img = img.crop((left, top, left + STAMP_W, top + STAMP_H))
    else:
        if src_ratio > target_ratio:
            new_w = STAMP_W
            new_h = int(new_w / src_ratio)
        else:
            new_h = STAMP_H
            new_w = int(src_ratio * new_h)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        canvas = Image.new("RGBA", (STAMP_W, STAMP_H), bg_color)
        x = (STAMP_W - new_w) // 2
        y = (STAMP_H - new_h) // 2
        canvas.paste(img, (x, y), img)
        img = canvas

    return img


# ── 生成ボタン ─────────────────────────────────────────────────
st.markdown("### 4. APNG生成")

if st.button("🚀 APNG を生成する", type="primary", use_container_width=True):
    frames = [resize_frame(img) for img in frames_raw]

    # APNG保存
    buf = io.BytesIO()
    frames[0].save(
        buf,
        format="PNG",
        save_all=True,
        append_images=frames[1:],
        loop=0,
        duration=duration_ms,
    )
    apng_bytes = buf.getvalue()
    size_kb = len(apng_bytes) / 1024

    # tab.png
    tab_img = frames[0].resize((TAB_W, TAB_H), Image.LANCZOS)
    tab_buf = io.BytesIO()
    tab_img.save(tab_buf, format="PNG")
    tab_bytes = tab_buf.getvalue()

    # サイズ警告
    if size_kb > MAX_KB:
        st.warning(
            f"⚠️ ファイルサイズが {size_kb:.1f}KB です。"
            f"LINE申請の上限は{MAX_KB}KBなので、フレーム数を減らすか画像を圧縮してください。"
        )
    else:
        st.success(f"✅ 生成完了！ファイルサイズ：{size_kb:.1f}KB（上限{MAX_KB}KB）")

    st.markdown("**生成されたAPNGプレビュー（1フレーム目）**")
    st.image(frames[0], width=320)

    col_a, col_b = st.columns(2)
    with col_a:
        st.download_button(
            label="📥 animation.apng をダウンロード",
            data=apng_bytes,
            file_name="animation.apng",
            mime="image/png",
            use_container_width=True,
        )
    with col_b:
        st.download_button(
            label="📥 tab.png をダウンロード",
            data=tab_bytes,
            file_name="tab.png",
            mime="image/png",
            use_container_width=True,
        )

st.divider()
st.caption("LINE Creators Market → https://creator.line.me/  |  アニメスタンプ仕様：320×270px / APNG / 300KB以内")
