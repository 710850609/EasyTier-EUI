/**
 * 轮询控制器类
 * 用于管理定时轮询任务，确保请求完成后再等待，避免请求堆积
 */
export class Poller {
  constructor(options = {}) {
    this.interval = options.interval || 3000
    this.immediate = options.immediate !== false
    this.onError = options.onError || null
    this._active = false
    this._timeoutId = null
    this._task = null
  }

  /**
   * 启动轮询
   * @param {Function} task - 异步任务函数
   */
  start(task) {
    if (this._active) return
    
    this._active = true
    this._task = task
    
    if (this.immediate) {
      this._poll()
    } else {
      this._scheduleNext()
    }
  }

  /**
   * 停止轮询
   */
  stop() {
    this._active = false
    if (this._timeoutId) {
      clearTimeout(this._timeoutId)
      this._timeoutId = null
    }
  }

  /**
   * 更新轮询间隔
   * @param {number} interval - 新的间隔时间（毫秒）
   */
  setInterval(interval) {
    this.interval = interval
    // 如果已有调度，取消它，用新间隔重新调度，使新间隔立即生效
    if (this._active && this._timeoutId) {
      clearTimeout(this._timeoutId)
      this._scheduleNext()
    }
  }

  /**
   * 获取当前状态
   */
  get isActive() {
    return this._active
  }

  /**
   * 内部轮询方法
   */
  async _poll() {
    if (!this._active) return

    try {
      await this._task()
    } catch (error) {
      console.error('轮询任务执行失败:', error)
      if (this.onError) {
        this.onError(error)
      }
    }

    if (this._active) {
      this._scheduleNext()
    }
  }

  /**
   * 调度下一次执行
   */
  _scheduleNext() {
    if (!this._active) return
    if (this._timeoutId) {
      clearTimeout(this._timeoutId)
    }
    this._timeoutId = setTimeout(() => this._poll(), this.interval)
  }
}

/**
 * 创建轮询器的工厂函数
 * @param {Object} options - 配置选项
 * @returns {Poller}
 */
export function createPoller(options) {
  return new Poller(options)
}