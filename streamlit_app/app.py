"""Streamlit frontend for the Document Intelligence System."""

import os
from typing import Any

import requests
import streamlit as st


DEFAULT_API_URL = "http://localhost:8000"
API_URL = os.getenv("API_URL", DEFAULT_API_URL).rstrip("/")
REQUEST_TIMEOUT_SECONDS = 60


def api_request(method: str, path: str, **kwargs: Any) -> requests.Response:
    """Send a request to the API and convert connection failures into UI errors."""
    try:
        return requests.request(
            method,
            f"{API_URL}{path}",
            timeout=REQUEST_TIMEOUT_SECONDS,
            **kwargs,
        )
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Unable to reach the verification API at {API_URL}. "
            "Start the API service and try again."
        ) from exc


def display_api_error(response: requests.Response) -> None:
    """Display a useful message for an unsuccessful API response."""
    try:
        detail = response.json().get("detail", response.text)
    except ValueError:
        detail = response.text
    st.error(f"API error ({response.status_code}): {detail}")


def render_sidebar() -> None:
    """Render service status and aggregate verification statistics."""
    st.sidebar.header("Service")
    st.sidebar.caption(API_URL)

    try:
        health_response = api_request("GET", "/health")
        if health_response.ok:
            health = health_response.json()
            st.sidebar.success("API online")
            st.sidebar.write(f"Model loaded: {health.get('model_loaded', False)}")
            st.sidebar.write(f"Database ready: {health.get('db_ready', False)}")
        else:
            st.sidebar.error("API is unhealthy")
    except RuntimeError as exc:
        st.sidebar.warning(str(exc))
        return

    try:
        stats_response = api_request("GET", "/stats")
        if stats_response.ok:
            stats = stats_response.json()
            st.sidebar.metric("Documents checked", stats.get("total") or 0)
            st.sidebar.metric(
                "Average confidence",
                f"{(stats.get('avg_confidence') or 0):.1%}",
            )
    except RuntimeError:
        pass


def render_result(result: dict[str, Any], image: Any) -> None:
    """Render a verification response."""
    label = result.get("label", "unknown")
    if result.get("is_uncertain"):
        st.warning(result.get("verdict", "Manual review recommended."))
    elif label == "tampered":
        st.error(result.get("verdict", "Possible tampering detected."))
    else:
        st.success(result.get("verdict", "No tampering detected."))

    columns = st.columns(4)
    columns[0].metric("Label", label.title())
    columns[1].metric("Confidence", f"{result.get('confidence', 0):.1%}")
    columns[2].metric("Authentic", f"{result.get('authentic_prob', 0):.1%}")
    columns[3].metric("Tampered", f"{result.get('tampered_prob', 0):.1%}")

    left, right = st.columns(2)
    with left:
        st.subheader("Uploaded document")
        st.image(image, use_container_width=True)
    with right:
        st.subheader("Analysis")
        st.write(f"ELA mean: **{result.get('ela_mean', 0):.2f}**")
        st.write(f"ELA region spread: **{result.get('ela_region_std', 0):.2f}**")
        st.write(f"OCR confidence: **{result.get('ocr_confidence', 0):.1%}**")
        st.write(f"Processing time: **{result.get('processing_time_ms', 0)} ms**")
        ocr_text = result.get("ocr_text", "")
        st.text_area("Extracted OCR text", ocr_text or "No text detected.", height=160)


def render_history() -> None:
    """Render recent verification history."""
    response = api_request("GET", "/history?limit=10")
    if response.ok:
        results = response.json().get("results", [])
        if results:
            st.dataframe(results, use_container_width=True, hide_index=True)
        else:
            st.info("No documents have been verified yet.")
    else:
        display_api_error(response)


def main() -> None:
    st.set_page_config(
        page_title="Document Intelligence System",
        page_icon="🔎",
        layout="wide",
    )
    st.title("Document Intelligence System")
    st.caption("Detect possible digital tampering with ELA and a Random Forest classifier.")
    render_sidebar()

    uploaded_file = st.file_uploader(
        "Upload a document image",
        type=["jpg", "jpeg", "png", "bmp", "tif", "tiff"],
        help="Maximum file size: 10 MB.",
    )

    if uploaded_file is not None:
        if st.button("Verify document", type="primary"):
            with st.spinner("Analyzing document..."):
                try:
                    response = api_request(
                        "POST",
                        "/verify",
                        files={
                            "file": (
                                uploaded_file.name,
                                uploaded_file.getvalue(),
                                uploaded_file.type or "application/octet-stream",
                            )
                        },
                    )
                except RuntimeError as exc:
                    st.error(str(exc))
                else:
                    if response.ok:
                        render_result(response.json(), uploaded_file)
                    else:
                        display_api_error(response)

    with st.expander("Recent verification history"):
        try:
            render_history()
        except RuntimeError as exc:
            st.info(str(exc))


if __name__ == "__main__":
    main()
