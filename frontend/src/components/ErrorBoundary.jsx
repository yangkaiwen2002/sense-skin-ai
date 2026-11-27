import { Component } from "react";
export default class ErrorBoundary extends Component {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    if (this.state.failed)
      return (
        <div className="page-shell state-panel" role="alert">
          <h1>页面暂时无法显示</h1>
          <p>已保存的研究记录不会因此丢失。重新加载后可继续使用。</p>
          <button
            className="action-primary"
            onClick={() => window.location.reload()}
          >
            重新加载页面
          </button>
          <a href="/">返回市场</a>
        </div>
      );
    return this.props.children;
  }
}
