import dataLoaderService, { MajorDirectionDefinition } from './DataLoaderService';

// 专业数据服务
// 处理 major_data_processed.json 数据的加载、筛选和查询

export interface LanguageRequirement {
  accepted: boolean;
  total_score: number | null;
  sub_scores: string | null;
}

export interface ApplicationRound {
  round: string;
  timeline: string;
}

export interface Curriculum {
  chinese_name: string;
  english_name: string;
}

export interface MajorData {
  major_id: string;
  detail_url: string;
  source_url: string;
  school_name: string;
  major_name_chinese: string;
  major_name_english: string;
  major_direction: string;
  location: string;
  qs_2026: number | null;
  qs_2025?: number | null;
  project_category: string;
  admission_time: string;
  project_duration: string;
  tuition: string;
  project_introduction: string;
  application_requirements: string;
  language_requirements: {
    toefl: LanguageRequirement;
    ielts: LanguageRequirement;
  };
  gmat_required: boolean;
  gre_required: boolean;
  application_rounds: ApplicationRound[];
  curriculum: Curriculum[];
  curriculum_count: number;
}

export interface SchoolInfo {
  school_name: string;
  major_count: number;
  qs_2026: number | null;
  qs_2025?: number | null;
  location: string;
  majors: MajorData[];
}

class MajorDataService {
  private majorData: MajorData[] = [];
  private schoolsMap: Map<string, SchoolInfo> = new Map();
  private isLoaded = false;

  // 加载数据
  async loadData(): Promise<void> {
    if (this.isLoaded) {
      return;
    }

    try {
      // 从public目录加载数据文件
      const response = await fetch('/data/major_data_processed.json');
      if (!response.ok) {
        throw new Error(`Failed to load data: ${response.statusText}`);
      }
      
      this.majorData = await response.json();
      this.buildSchoolsMap();
      this.isLoaded = true;
      
      console.log(`Loaded ${this.majorData.length} majors from ${this.schoolsMap.size} schools`);
    } catch (error) {
      console.error('Error loading major data:', error);
      throw error;
    }
  }

  // 构建学校映射
  private buildSchoolsMap(): void {
    this.schoolsMap.clear();
    
    this.majorData.forEach(major => {
      const schoolName = major.school_name;
      
      if (!this.schoolsMap.has(schoolName)) {
        this.schoolsMap.set(schoolName, {
          school_name: schoolName,
          major_count: 0,
          qs_2026: major.qs_2026,
          qs_2025: major.qs_2025,
          location: major.location,
          majors: []
        });
      }
      
      const school = this.schoolsMap.get(schoolName)!;
      school.majors.push(major);
      school.major_count = school.majors.length;
    });
  }

  // 获取所有学校列表
  async getSchools(): Promise<SchoolInfo[]> {
    await this.loadData();
    
    return Array.from(this.schoolsMap.values())
      .sort((a, b) => {
        // 按QS 2026排名排序，排名越小越靠前，null值排在最后
        if (a.qs_2026 === null && b.qs_2026 === null) {
          return a.school_name.localeCompare(b.school_name, 'zh-CN');
        }
        if (a.qs_2026 === null) return 1;
        if (b.qs_2026 === null) return -1;
        if (a.qs_2026 !== b.qs_2026) {
          return a.qs_2026 - b.qs_2026;
        }
        // 排名相同时按学校名称排序
        return a.school_name.localeCompare(b.school_name, 'zh-CN');
      });
  }

  // 根据学校名称获取学校信息
  async getSchoolByName(schoolName: string): Promise<SchoolInfo | null> {
    await this.loadData();
    return this.schoolsMap.get(schoolName) || null;
  }

  // 获取某个学校的所有专业
  async getMajorsBySchool(schoolName: string): Promise<MajorData[]> {
    await this.loadData();
    const school = this.schoolsMap.get(schoolName);
    return school ? school.majors : [];
  }

  // 获取所有专业列表
  async getAllMajors(): Promise<MajorData[]> {
    await this.loadData();
    return [...this.majorData];
  }

  // 根据专业ID获取专业详情
  async getMajorById(majorId: string): Promise<MajorData | null> {
    await this.loadData();
    return this.majorData.find(major => major.major_id === majorId) || null;
  }

  // 搜索专业
  async searchMajors(query: string): Promise<MajorData[]> {
    await this.loadData();
    
    const lowerQuery = query.toLowerCase();
    return this.majorData.filter(major => 
      major.major_name_chinese.toLowerCase().includes(lowerQuery) ||
      major.major_name_english.toLowerCase().includes(lowerQuery) ||
      major.school_name.toLowerCase().includes(lowerQuery) ||
      major.major_direction.toLowerCase().includes(lowerQuery)
    );
  }

  // 按专业方向筛选
  async getMajorsByDirection(direction: string): Promise<MajorData[]> {
    await this.loadData();
    return this.majorData.filter(major => major.major_direction === direction);
  }

  // 获取所有专业方向
  async getMajorDirections(): Promise<string[]> {
    await this.loadData();
    const availableDirections = new Set(
      this.majorData
        .map(major => major.major_direction)
        .filter(direction => direction && direction.trim() !== '')
    );

    const taxonomyDirections: MajorDirectionDefinition[] = await dataLoaderService.loadMajorDirections();
    const filtered = taxonomyDirections.filter(direction => availableDirections.has(direction.name));

    if (filtered.length === 0) {
      return Array.from(availableDirections).sort((a, b) => a.localeCompare(b, 'zh-CN'));
    }

    return filtered.map(direction => direction.name);
  }

  // 获取所有地区
  async getLocations(): Promise<string[]> {
    await this.loadData();
    const locations = new Set(this.majorData.map(major => major.location));
    return Array.from(locations).filter(location => location && location.trim() !== '').sort();
  }

  // 按QS排名分组获取专业
  async getMajorsByQSRanking(rankingType: 'qs_2026' | 'qs_2025' = 'qs_2026'): Promise<{[key: string]: MajorData[]}> {
    await this.loadData();

    const groups: {[key: string]: MajorData[]} = {
      'QS前10': [],
      'QS前50': [],
      'QS前100': [],
      'QS前200': [],
      'QS前500': [],
      'QS500+': [],
      '未排名': []
    };

    this.majorData.forEach(major => {
      const ranking = major[rankingType];
      if (ranking === null || ranking === undefined) {
        groups['未排名'].push(major);
      } else if (ranking <= 10) {
        groups['QS前10'].push(major);
      } else if (ranking <= 50) {
        groups['QS前50'].push(major);
      } else if (ranking <= 100) {
        groups['QS前100'].push(major);
      } else if (ranking <= 200) {
        groups['QS前200'].push(major);
      } else if (ranking <= 500) {
        groups['QS前500'].push(major);
      } else {
        groups['QS500+'].push(major);
      }
    });

    return groups;
  }

  // 按专业方向分组获取专业
  async getMajorsByDirectionGroup(): Promise<{[key: string]: MajorData[]}> {
    await this.loadData();

    const groupsByDirection: Map<string, MajorData[]> = new Map();

    this.majorData.forEach(major => {
      const direction = major.major_direction || '其他';
      if (!groupsByDirection.has(direction)) {
        groupsByDirection.set(direction, []);
      }
      groupsByDirection.get(direction)!.push(major);
    });

    const orderedGroups: {[key: string]: MajorData[]} = {};
    const taxonomyDirections = await dataLoaderService.loadMajorDirections();

    taxonomyDirections.forEach(direction => {
      const majors = groupsByDirection.get(direction.name);
      if (majors && majors.length > 0) {
        orderedGroups[`${direction.groupName}｜${direction.name}`] = majors;
        groupsByDirection.delete(direction.name);
      }
    });

    if (groupsByDirection.size > 0) {
      Array.from(groupsByDirection.entries())
        .sort((a, b) => a[0].localeCompare(b[0], 'zh-CN'))
        .forEach(([directionName, majors]) => {
          orderedGroups[directionName] = majors;
        });
    }

    return orderedGroups;
  }

  // 按地区分组获取专业
  async getMajorsByLocationGroup(): Promise<{[key: string]: MajorData[]}> {
    await this.loadData();

    const groups: {[key: string]: MajorData[]} = {};

    this.majorData.forEach(major => {
      const location = major.location || '其他';
      if (!groups[location]) {
        groups[location] = [];
      }
      groups[location].push(major);
    });

    return groups;
  }

  // 获取统计信息
  async getStatistics() {
    await this.loadData();

    const directions = await this.getMajorDirections();
    const schools = await this.getSchools();
    const locations = await this.getLocations();

    return {
      totalMajors: this.majorData.length,
      totalSchools: schools.length,
      totalDirections: directions.length,
      totalLocations: locations.length,
      topSchoolsByMajorCount: schools
        .sort((a, b) => b.major_count - a.major_count)
        .slice(0, 10)
    };
  }
}

// 导出单例实例
export const majorDataService = new MajorDataService();
export default majorDataService;
