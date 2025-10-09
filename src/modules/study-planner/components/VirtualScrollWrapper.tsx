'use client';

/**
 * VirtualScrollWrapper - 虚拟滚动包装器组件 (性能优化版)
 * 
 * Linus的原则：
 * 1. 先让它工作，再让它完美
 * 2. 简单可靠比复杂智能更重要
 * 3. 用最直接的方法解决问题
 * 4. 性能优化是用户体验的关键
 */

import React, { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import { FixedSizeList as List } from 'react-window';
import { Input, Spin } from 'antd';
import { SearchOutlined } from '@ant-design/icons';

const { Search } = Input;

// 组件属性接口
export interface VirtualScrollWrapperProps {
  data: string[];
  height?: number;
  itemHeight?: number;
  onSelect?: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  notFoundContent?: React.ReactNode;
  showSearch?: boolean;
  filterOption?: boolean;
  allowClear?: boolean;
  loading?: boolean;
}

// 列表项渲染器属性
interface ListItemProps {
  index: number;
  style: React.CSSProperties;
  data: {
    items: string[];
    onSelect: (value: string) => void;
    itemHeight: number;
  };
}

/**
 * 虚拟滚动包装器组件
 * 
 * 功能：
 * 1. 高性能渲染大量数据
 * 2. 支持实时搜索过滤
 * 3. 支持选项选择
 * 4. 与 Ant Design 风格一致
 */
const VirtualScrollWrapper: React.FC<VirtualScrollWrapperProps> = ({
  data,
  height = 300,
  itemHeight = 32,
  onSelect,
  placeholder = '搜索...',
  disabled = false,
  notFoundContent = '未找到匹配的选项',
  showSearch = true,
  filterOption = true,
  allowClear = true,
  loading = false,
}) => {
  // 搜索状态
  const [searchValue, setSearchValue] = useState('');
  const [debouncedSearchValue, setDebouncedSearchValue] = useState('');
  
  // 防抖定时器引用
  const debounceTimerRef = useRef<NodeJS.Timeout | undefined>(undefined);
  
  // 防抖搜索效果
  useEffect(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    
    debounceTimerRef.current = setTimeout(() => {
      setDebouncedSearchValue(searchValue);
    }, 150); // 150ms防抖延迟
    
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [searchValue]);

  // 过滤后的数据 (使用防抖后的搜索值)
  const filteredData = useMemo(() => {
    if (!filterOption || !debouncedSearchValue.trim()) {
      return data;
    }
    
    const searchLower = debouncedSearchValue.toLowerCase();
    return data.filter(item => 
      item.toLowerCase().includes(searchLower)
    );
  }, [data, debouncedSearchValue, filterOption]);

  // 处理搜索
  const handleSearch = useCallback((value: string) => {
    setSearchValue(value);
  }, []);

  // 处理选项选择
  const handleItemSelect = useCallback((value: string) => {
    if (onSelect && !disabled) {
      onSelect(value);
    }
  }, [onSelect, disabled]);

  // 预计算样式对象
  const itemStyles = useMemo(() => ({
    base: {
      padding: '6px 12px',
      borderBottom: '1px solid #f0f0f0',
      display: 'flex',
      alignItems: 'center',
      fontSize: '14px',
      lineHeight: '20px',
      userSelect: 'none' as const,
    },
    disabled: {
      cursor: 'not-allowed',
      backgroundColor: '#f5f5f5',
    },
    enabled: {
      cursor: 'pointer',
      backgroundColor: 'transparent',
    },
    hover: {
      backgroundColor: '#f5f5f5',
    }
  }), []);

  // 列表项渲染器 (性能优化版)
  const renderItem = useCallback(({ index, style, data }: ListItemProps) => {
    const item = data.items[index];
    if (!item) return null;

    const baseStyle = {
      ...style,
      ...itemStyles.base,
      ...(disabled ? itemStyles.disabled : itemStyles.enabled),
    };

    return (
      <div
        style={baseStyle}
        onClick={() => handleItemSelect(item)}
        onMouseEnter={(e) => {
          if (!disabled) {
            e.currentTarget.style.backgroundColor = itemStyles.hover.backgroundColor!;
          }
        }}
        onMouseLeave={(e) => {
          if (!disabled) {
            e.currentTarget.style.backgroundColor = itemStyles.enabled.backgroundColor!;
          }
        }}
      >
        {item}
      </div>
    );
  }, [handleItemSelect, disabled, itemStyles]);

  // 如果没有数据，显示空状态
  if (data.length === 0) {
    return (
      <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {loading ? <Spin size="small" /> : notFoundContent}
      </div>
    );
  }

  return (
    <div style={{ border: '1px solid #d9d9d9', borderRadius: '6px', overflow: 'hidden' }}>
      {/* 搜索框 */}
      {showSearch && (
        <div style={{ padding: '8px', borderBottom: '1px solid #f0f0f0' }}>
          <Search
            placeholder={placeholder}
            value={searchValue}
            onChange={(e) => handleSearch(e.target.value)}
            allowClear={allowClear}
            disabled={disabled}
            loading={loading}
            prefix={<SearchOutlined />}
            size="small"
          />
        </div>
      )}
      
      {/* 虚拟滚动列表 */}
      <div style={{ height: showSearch ? height - 60 : height }}>
        {filteredData.length === 0 ? (
          <div style={{ 
            height: '100%', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            color: '#999',
            fontSize: '14px'
          }}>
            {notFoundContent}
          </div>
        ) : (
          <List
            height={showSearch ? height - 60 : height}
            itemCount={filteredData.length}
            itemSize={itemHeight}
            width="100%"
            itemData={{
              items: filteredData,
              onSelect: handleItemSelect,
              itemHeight,
            }}
            overscanCount={5} // 预渲染5个项目，提升滚动性能
            useIsScrolling={false} // 禁用滚动状态检测，提升性能
          >
            {renderItem}
          </List>
        )}
      </div>
    </div>
  );
};

// 使用React.memo优化组件重渲染
const MemoizedVirtualScrollWrapper = React.memo(VirtualScrollWrapper, (prevProps, nextProps) => {
  // 自定义比较函数，只在关键属性变化时重渲染
  return (
    prevProps.data === nextProps.data &&
    prevProps.height === nextProps.height &&
    prevProps.itemHeight === nextProps.itemHeight &&
    prevProps.disabled === nextProps.disabled &&
    prevProps.loading === nextProps.loading &&
    prevProps.showSearch === nextProps.showSearch &&
    prevProps.filterOption === nextProps.filterOption &&
    prevProps.placeholder === nextProps.placeholder &&
    prevProps.notFoundContent === nextProps.notFoundContent
  );
});

export default MemoizedVirtualScrollWrapper;

