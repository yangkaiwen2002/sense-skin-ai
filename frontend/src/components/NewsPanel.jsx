import { Newspaper, ArrowsClockwise, ArrowUpRight } from '@phosphor-icons/react'
import Button from './ui/Button'
import { formatDate } from '../utils/formatters'

export default function NewsPanel({ news = [], loading, failed, syncing, disabled, onSync, onRetry }) {
  return (
    <section className="news-panel" aria-label="官方事件来源">
      <details>
        <summary className="news-summary">
          <span className="news-label"><Newspaper size={18} />官方公告</span>
          <span className="news-headline">{loading ? '正在读取公告…' : failed ? '公告暂时无法载入' : news[0]?.title || '尚未同步官方公告'}</span>
          <span className="news-date">{news[0] && formatDate(news[0].event_date)}</span>
          <span className="news-expand"><span className="when-closed">展开</span><span className="when-open">收起</span></span>
        </summary>
        <div className="news-body">
          <div className="news-tools">
            <p>全局市场背景 · 价格影响待评估</p>
            <Button size="sm" disabled={disabled} loading={syncing} onClick={onSync}><ArrowsClockwise size={15} />{syncing ? '同步中' : '同步官方新闻'}</Button>
          </div>
          {failed && <p role="alert" className="notice notice-error">公告加载失败。<button onClick={onRetry}>重新加载</button></p>}
          {!failed && !loading && !news.length && <p className="muted-copy">点击同步，从 Steam 获取官方公告及原文链接。</p>}
          {news.slice(0, 5).map(event => (
            <article className="news-row" key={event.id}>
              <time>{formatDate(event.event_date)}</time>
              <div><h3>{event.title}</h3><p>{event.summary}</p></div>
              {/^https:\/\//.test(event.source_url || '') && <a href={event.source_url} target="_blank" rel="noreferrer" aria-label={`查看原文：${event.title}`}>原文<ArrowUpRight size={14} /></a>}
            </article>
          ))}
        </div>
      </details>
    </section>
  )
}
