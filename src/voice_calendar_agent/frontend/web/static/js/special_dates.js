/**
 * 特殊日期配置文件
 *
 * 管理法定节假日、调休休息、补班、二十四节气四类特殊日期。
 * 与后端/数据库无关，纯前端静态数据，支持按年扩展。
 *
 * 数据结构：
 *   "YYYY-MM-DD": {
 *     type:  "holiday" | "term" | "makeup" | "rest",
 *     name:  显示标签文字,
 *     image?: 背景图片路径（仅 holiday / term 有）
 *   }
 *
 * 优先级（Q5-A）：holiday > term > makeup > rest
 * 同一天只保留优先级最高的类型。
 */

const SPECIAL_DATES = {

  // ════════════════════════════════════════════
  // 一月
  // ════════════════════════════════════════════
  "2026-01-01": { type: "holiday", name: "元旦",     image: "images/jieri/元旦.png" },
  "2026-01-02": { type: "rest",    name: "休息" },
  "2026-01-03": { type: "rest",    name: "休息" },
  "2026-01-04": { type: "makeup",  name: "补班" },
  "2026-01-05": { type: "term",    name: "小寒",     image: "images/24_jieqi/23_小寒.png" },
  "2026-01-20": { type: "term",    name: "大寒",     image: "images/24_jieqi/24_大寒.png" },

  // ════════════════════════════════════════════
  // 二月
  // ════════════════════════════════════════════
  "2026-02-04": { type: "term",    name: "立春",     image: "images/24_jieqi/1_立春.png" },
  "2026-02-14": { type: "makeup",  name: "补班" },
  "2026-02-14": { type: "holiday",  name: "情人节",   image:"images/jieri/情人节.png" },
  "2026-02-15": { type: "holiday", name: "春节",     image: "images/jieri/春节.png" },
  "2026-02-16": { type: "rest",    name: "休息" },
  "2026-02-17": { type: "rest",    name: "休息" },
  "2026-02-18": { type: "term",    name: "雨水",     image: "images/24_jieqi/2_雨水.png" },
  "2026-02-19": { type: "rest",    name: "休息" },
  "2026-02-20": { type: "rest",    name: "休息" },
  "2026-02-21": { type: "rest",    name: "休息" },
  "2026-02-22": { type: "rest",    name: "休息" },
  "2026-02-23": { type: "rest",    name: "休息" },
  "2026-02-28": { type: "makeup",  name: "补班" },

  // ════════════════════════════════════════════
  // 三月
  // ════════════════════════════════════════════
  "2026-03-05": { type: "term",    name: "惊蛰",     image: "images/24_jieqi/3_惊蛰.png" },
  "2026-03-08": { type: "holiday", name: "妇女节",    image: "images/jieri/妇女节.png" },
  "2026-03-20": { type: "term",    name: "春分",     image: "images/24_jieqi/4_春分.png" },

  // ════════════════════════════════════════════
  // 四月
  // ════════════════════════════════════════════
  "2026-04-04": { type: "holiday", name: "清明节",   image: "images/jieri/清明节.png" },
  "2026-04-06": { type: "rest",    name: "休息" },
  "2026-04-20": { type: "term",    name: "谷雨",     image: "images/24_jieqi/6_谷雨.png" },

  // ════════════════════════════════════════════
  // 五月
  // ════════════════════════════════════════════
  "2026-05-01": { type: "holiday", name: "劳动节",   image: "images/jieri/劳动节.png" },
  "2026-05-02": { type: "rest",    name: "休息" },
  "2026-05-03": { type: "rest",    name: "休息" },
  "2026-05-04": { type: "rest",    name: "休息" },
  "2026-05-05": { type: "term",    name: "立夏",     image: "images/24_jieqi/7_立夏.png" },    // 立夏 + 休息重叠 → term 优先
  "2026-05-09": { type: "makeup",  name: "补班" },
  "2026-05-21": { type: "term",    name: "小满",     image: "images/24_jieqi/8_小满.png" },

  // ════════════════════════════════════════════
  // 六月
  // ════════════════════════════════════════════
  "2026-06-01": { type: "holiday",    name: "儿童节",     image: "images/jieri/儿童节.png" },
  "2026-06-05": { type: "term",    name: "芒种",     image: "images/24_jieqi/9_芒种.png" },
  "2026-06-19": { type: "holiday", name: "端午节",   image: "images/jieri/端午节.png" },
  "2026-06-20": { type: "rest",    name: "休息" },
  "2026-06-21": { type: "term",    name: "夏至",     image: "images/24_jieqi/10_夏至.png" },  // 夏至 + 休息重叠 → term 优先

  // ════════════════════════════════════════════
  // 七月
  // ════════════════════════════════════════════
  "2026-07-07": { type: "term",    name: "小暑",     image: "images/24_jieqi/11_小暑.png" },
  "2026-07-23": { type: "term",    name: "大暑",     image: "images/24_jieqi/12_大暑.png" },

  // ════════════════════════════════════════════
  // 八月
  // ════════════════════════════════════════════
  "2026-08-07": { type: "term",    name: "立秋",     image: "images/24_jieqi/13_立秋.png" },
  "2026-08-23": { type: "term",    name: "处暑",     image: "images/24_jieqi/14_处暑.png" },

  // ════════════════════════════════════════════
  // 九月
  // ════════════════════════════════════════════
  "2026-09-07": { type: "term",    name: "白露",     image: "images/24_jieqi/15_白露.png" },
  "2026-09-20": { type: "makeup",  name: "补班" },
  "2026-09-23": { type: "term",    name: "秋分",     image: "images/24_jieqi/16_秋分.png" },
  "2026-09-25": { type: "holiday", name: "中秋节",   image: "images/jieri/中秋节.png" },
  "2026-09-26": { type: "rest",    name: "休息" },
  "2026-09-27": { type: "rest",    name: "休息" },

  // ════════════════════════════════════════════
  // 十月
  // ════════════════════════════════════════════
  "2026-10-01": { type: "holiday", name: "国庆节",   image: "images/jieri/国庆节.png" },
  "2026-10-02": { type: "rest",    name: "休息" },
  "2026-10-03": { type: "rest",    name: "休息" },
  "2026-10-04": { type: "rest",    name: "休息" },
  "2026-10-05": { type: "rest",    name: "休息" },
  "2026-10-06": { type: "rest",    name: "休息" },
  "2026-10-07": { type: "rest",    name: "休息" },
  "2026-10-08": { type: "term",    name: "寒露",     image: "images/24_jieqi/17_寒露.png" },
  "2026-10-10": { type: "makeup",  name: "补班" },
  "2026-10-23": { type: "term",    name: "霜降",     image: "images/24_jieqi/18_霜降.png" },

  // ════════════════════════════════════════════
  // 十一月
  // ════════════════════════════════════════════
  "2026-11-07": { type: "term",    name: "立冬",     image: "images/24_jieqi/19_立冬.png" },
  "2026-11-22": { type: "term",    name: "小雪",     image: "images/24_jieqi/20_小雪.png" },

  // ════════════════════════════════════════════
  // 十二月
  // ════════════════════════════════════════════
  "2026-12-07": { type: "term",    name: "大雪",     image: "images/24_jieqi/21_大雪.png" },
  "2026-12-22": { type: "term",    name: "冬至",     image: "images/24_jieqi/22_冬至.png" },
};

/** 类型 → 标签颜色 CSS 类映射 */
const LABEL_COLORS = {
  holiday: "bg-red-500/15 text-red-400",
  term:    "bg-emerald-500/15 text-emerald-400",
  makeup:  "bg-amber-500/15 text-amber-400",
  rest:    "bg-slate-500/15 text-slate-400",
};

/**
 * 查询指定日期的特殊日期信息
 * @param {string} dateStr - "YYYY-MM-DD"
 * @returns {{type: string, name: string, image?: string} | null}
 */
function getSpecialDate(dateStr) {
  return SPECIAL_DATES[dateStr] || null;
}

/**
 * 获取指定日期的背景图片 URL
 * @param {string} dateStr - "YYYY-MM-DD"
 * @returns {string | null}
 */
function getSpecialImage(dateStr) {
  const sd = SPECIAL_DATES[dateStr];
  return sd && sd.image ? "/static/" + sd.image : null;
}
