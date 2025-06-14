import streamlit as st
import streamlit.components.v1 as components

with open("../frontend/index.html", "r", encoding="utf-8") as f:
    html = f.read()

components.html(html, height=600, scrolling=True)
