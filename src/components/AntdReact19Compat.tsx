'use client';

import { useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import { unstableSetRender } from 'antd/es/config-provider/UnstableContext';

/**
 * Configures Ant Design to use React 19's `createRoot` API, preventing compatibility warnings.
 */
const AntdReact19Compat = () => {
  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    unstableSetRender((node, container) => {
      const root = createRoot(container);
      root.render(node);
      return () => root.unmount();
    });
  }, []);

  return null;
};

export default AntdReact19Compat;
