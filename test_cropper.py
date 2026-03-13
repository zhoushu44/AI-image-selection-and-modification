import streamlit as st
from streamlit_cropper import st_cropper
from PIL import Image

st.set_page_config(layout="wide")
st.title("测试 streamlit-cropper 鼠标框选")

uploaded_file = st.file_uploader("上传图片", type=['png', 'jpg', 'jpeg'])

if uploaded_file is not None:
    img = Image.open(uploaded_file)
    
    st.subheader("鼠标框选测试")
    st.info("在下方图片上拖拽鼠标进行框选")
    
    cropped_img = st_cropper(img, aspect_ratio=None, box_color='#1677FF')
    
    st.subheader("框选结果")
    st.image(cropped_img, caption="框选后的图片", use_container_width=True)
