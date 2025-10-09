/**
 * DataLoaderService - 数据加载服务
 * 
 * Linus的原则：
 * 1. 先让它工作，再让它完美
 * 2. 简单可靠比复杂智能更重要
 * 3. 用最直接的方法解决问题
 */

import frontendData from '../data/frontend_data.json';

// 数据接口
export interface DataMetrics {
  universitiesCount: number;
  majorsCount: number;
  targetMajorsCount: number;
  totalDataSize: number;
}

/**
 * 数据加载服务
 * 
 * 职责：
 * 1. 从JSON文件加载院校/专业信息
 * 2. 提供数据完整性验证
 * 3. 提供数据指标统计
 */
export class DataLoaderService {
  /**
   * 加载院校数据
   * Linus: "直接返回JSON数据，但要验证数据完整性"
   */
  async loadUniversities(): Promise<string[]> {
    try {
      const universities = frontendData.universities;
      
      // 验证数据完整性
      if (!universities || universities.length < 500) {
        throw new Error(`院校数据不完整：期望至少500所，实际${universities?.length || 0}所`);
      }

      return universities;
    } catch (error) {
      console.error('加载院校数据失败:', error);
      throw error; // 构建时数据加载失败，应用无法启动
    }
  }

  /**
   * 加载专业数据
   * Linus: "复制上面的逻辑，但针对专业数据"
   */
  async loadMajors(): Promise<string[]> {
    try {
      const majors = frontendData.majors;
      
      // 验证数据完整性
      if (!majors || majors.length < 500) {
        throw new Error(`专业数据不完整：期望至少500个，实际${majors?.length || 0}个`);
      }

      return majors;
    } catch (error) {
      console.error('加载专业数据失败:', error);
      throw error; // 构建时数据加载失败，应用无法启动
    }
  }

  /**
   * 加载国家数据
   * 注意：JSON文件中没有countries字段，返回硬编码的国家列表
   */
  async loadCountries(): Promise<string[]> {
    // 返回硬编码的国家列表，与原有逻辑保持一致
    return [
      "香港","新加坡", "美国", "英国", "加拿大", "澳大利亚",  "德国", "法国", "日本", "韩国", 
      "荷兰", "瑞士", "瑞典", "丹麦", "挪威", "芬兰", "意大利", "西班牙", "葡萄牙", "比利时", 
      "奥地利", "爱尔兰", "新西兰", "马来西亚", "泰国", "印度", "俄罗斯", "乌克兰", "波兰", 
      "捷克", "匈牙利", "罗马尼亚", "保加利亚", "克罗地亚", "斯洛文尼亚", "爱沙尼亚", 
      "拉脱维亚", "立陶宛", "马耳他", "塞浦路斯", "希腊", "土耳其", "以色列", "阿联酋", 
      "沙特阿拉伯", "卡塔尔", "科威特", "巴林", "阿曼", "约旦", "黎巴嫩", "叙利亚", 
      "伊拉克", "伊朗", "阿富汗", "巴基斯坦", "孟加拉国", "斯里兰卡", "尼泊尔", "不丹", 
      "缅甸", "老挝", "柬埔寨", "越南", "菲律宾", "印度尼西亚", "文莱", "东帝汶", 
      "蒙古", "朝鲜", "韩国", "日本", "台湾", "澳门"
    ];
  }

  /**
   * 加载目标专业数据
   * 注意：JSON文件中的target_majors是按类别组织的对象，需要转换为扁平数组
   */
  async loadTargetMajors(): Promise<string[]> {
    try {
      const targetMajorsObj = frontendData.target_majors;
      
      // 验证数据完整性
      if (!targetMajorsObj || typeof targetMajorsObj !== 'object') {
        throw new Error('目标专业数据结构不正确');
      }

      // 将按类别组织的对象转换为扁平数组
      const targetMajors: string[] = [];
      Object.values(targetMajorsObj).forEach(category => {
        if (Array.isArray(category)) {
          targetMajors.push(...category);
        }
      });

      // 验证转换后的数据完整性
      if (targetMajors.length < 50) {
        throw new Error(`目标专业数据不完整：期望至少50个，实际${targetMajors.length}个`);
      }

      return targetMajors;
    } catch (error) {
      console.error('加载目标专业数据失败:', error);
      throw error;
    }
  }

  /**
   * 验证数据完整性
   * Linus: "验证要简单明确"
   */
  validateDataIntegrity(): boolean {
    try {
      const universities = frontendData.universities;
      const majors = frontendData.majors;
      const targetMajorsObj = frontendData.target_majors;

      // 验证基本数据结构
      if (!universities || !majors || !targetMajorsObj) {
        return false;
      }

      // 验证数据长度
      if (universities.length < 500 || majors.length < 500) {
        return false;
      }

      // 验证target_majors结构
      if (typeof targetMajorsObj !== 'object') {
        return false;
      }

      return true;
    } catch {
      return false;
    }
  }

  /**
   * 获取数据指标
   * Linus: "指标要实用，不要过度设计"
   */
  getDataMetrics(): DataMetrics {
    const universities = frontendData.universities || [];
    const majors = frontendData.majors || [];
    const targetMajorsObj = frontendData.target_majors || {};

    // 计算target_majors的总数量
    let targetMajorsCount = 0;
    if (typeof targetMajorsObj === 'object') {
      Object.values(targetMajorsObj).forEach(category => {
        if (Array.isArray(category)) {
          targetMajorsCount += category.length;
        }
      });
    }

    return {
      universitiesCount: universities.length,
      majorsCount: majors.length,
      targetMajorsCount: targetMajorsCount,
      totalDataSize: JSON.stringify(frontendData).length,
    };
  }

  /**
   * 预加载核心数据，用于测试或启动时预热
   */
  async preloadAll(): Promise<void> {
    await Promise.all([
      this.loadUniversities(),
      this.loadMajors(),
      this.loadCountries(),
      this.loadTargetMajors(),
    ]);
  }
}

// 导出单例实例
export const dataLoaderService = new DataLoaderService();
export default dataLoaderService;
