/**
 * DataLoaderService - 数据加载服务
 * 
 * Linus的原则：
 * 1. 先让它工作，再让它完美
 * 2. 简单可靠比复杂智能更重要
 * 3. 用最直接的方法解决问题
 */

import frontendData from '../data/frontend_data.json';
import majorTaxonomy from '../data/major_taxonomy.json';

// 数据接口
export interface DataMetrics {
  universitiesCount: number;
  majorsCount: number;
  majorDirectionsCount: number;
  majorGroupsCount: number;
  totalDataSize: number;
}

export interface MajorGroupDefinition {
  id: string;
  name: string;
  order: number;
}

export interface MajorDirectionDefinition {
  id: string;
  name: string;
  groupId: string;
  groupName: string;
  groupOrder: number;
  order: number;
  aliases: string[];
  keywords: string[];
  stats: {
    major_count: number;
  };
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
   * 注意：统一使用 major_taxonomy.json 中的数据源
   */
  async loadTargetMajors(): Promise<string[]> {
    const directions = await this.loadMajorDirections();
    return directions.map(direction => direction.name);
  }

  /**
   * 加载专业方向定义列表
   */
  async loadMajorDirections(): Promise<MajorDirectionDefinition[]> {
    try {
      const groups = this.getMajorDirectionGroups();
      const groupMap = new Map(groups.map(group => [group.id, group]));

      if (!Array.isArray(majorTaxonomy.directions) || majorTaxonomy.directions.length === 0) {
        throw new Error('专业方向数据为空，请检查 major_taxonomy.json');
      }

      const directions = majorTaxonomy.directions.map(direction => {
        const group = groupMap.get(direction.group_id);
        if (!group) {
          throw new Error(`专业方向 ${direction.name} 缺少有效的 group 定义`); 
        }
        return {
          id: direction.id,
          name: direction.name,
          groupId: direction.group_id,
          groupName: group.name,
          groupOrder: group.order,
          order: direction.order,
          aliases: direction.aliases ?? [],
          keywords: direction.keywords ?? [],
          stats: direction.stats ?? { major_count: 0 }
        } as MajorDirectionDefinition;
      });

      // 按 groupOrder -> order -> name 排序，保证展示顺序稳定
      directions.sort((a, b) => {
        if (a.groupOrder !== b.groupOrder) {
          return a.groupOrder - b.groupOrder;
        }
        if (a.order !== b.order) {
          return a.order - b.order;
        }
        return a.name.localeCompare(b.name, 'zh-CN');
      });

      return directions;
    } catch (error) {
      console.error('加载专业方向定义失败:', error);
      throw error;
    }
  }

  /**
   * 加载专业方向分组信息
   */
  getMajorDirectionGroups(): MajorGroupDefinition[] {
    const groups = majorTaxonomy.groups;
    if (!Array.isArray(groups) || groups.length === 0) {
      throw new Error('专业方向分组数据缺失，请检查 major_taxonomy.json');
    }

    return [...groups].sort((a, b) => {
      if (a.order !== b.order) {
        return a.order - b.order;
      }
      return a.name.localeCompare(b.name, 'zh-CN');
    });
  }

  /**
   * 验证数据完整性
   * Linus: "验证要简单明确"
   */
  validateDataIntegrity(): boolean {
    try {
      const universities = frontendData.universities;
      const majors = frontendData.majors;
      const groups = majorTaxonomy.groups;
      const directions = majorTaxonomy.directions;

      // 验证基本数据结构
      if (!universities || !majors || !groups || !directions) {
        return false;
      }

      // 验证数据长度
      if (universities.length < 500 || majors.length < 500) {
        return false;
      }

      if (!Array.isArray(groups) || groups.length === 0) {
        return false;
      }

      if (!Array.isArray(directions) || directions.length < 50) {
        return false;
      }

      const groupIds = new Set(groups.map(group => group.id));
      const hasInvalidDirection = directions.some(direction => !groupIds.has(direction.group_id));
      if (hasInvalidDirection) {
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
    const groups = Array.isArray(majorTaxonomy.groups) ? majorTaxonomy.groups : [];
    const directions = Array.isArray(majorTaxonomy.directions) ? majorTaxonomy.directions : [];

    return {
      universitiesCount: universities.length,
      majorsCount: majors.length,
      majorDirectionsCount: directions.length,
      majorGroupsCount: groups.length,
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
      this.loadMajorDirections(),
      this.loadTargetMajors(),
    ]);
  }
}

// 导出单例实例
export const dataLoaderService = new DataLoaderService();
export default dataLoaderService;
