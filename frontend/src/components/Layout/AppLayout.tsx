import { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Layout,
  Menu,
  Button,
  Avatar,
  Dropdown,
  Typography,
  Space,
  Breadcrumb,
} from 'antd';
import type { MenuProps } from 'antd';
import {
  DashboardOutlined,
  FileTextOutlined,
  UploadOutlined,
  CheckCircleOutlined,
  AppstoreOutlined,
  ShopOutlined,
  EnvironmentOutlined,
  BarChartOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import { useAuth } from '../../hooks/useAuth';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

type MenuItem = Required<MenuProps>['items'][number];

function getItem(
  label: React.ReactNode,
  key: string,
  icon?: React.ReactNode,
  children?: MenuItem[]
): MenuItem {
  return { key, icon, children, label } as MenuItem;
}

const menuItems: MenuItem[] = [
  getItem('Dashboard', '/', <DashboardOutlined />),
  getItem('Documents', '/documents', <FileTextOutlined />, [
    getItem('All Documents', '/documents', <FileTextOutlined />),
    getItem('Upload', '/documents/upload', <UploadOutlined />),
  ]),
  getItem('Review Queue', '/review', <CheckCircleOutlined />),
  getItem('Materials', '/materials', <AppstoreOutlined />),
  getItem('Providers', '/providers', <ShopOutlined />),
  getItem('Destinations', '/destinations', <EnvironmentOutlined />),
  getItem('Analytics', '/analytics', <BarChartOutlined />),
];

const adminMenuItems: MenuItem[] = [
  ...menuItems,
  getItem('Users', '/users', <UserOutlined />),
];

const breadcrumbMap: Record<string, string> = {
  '/': 'Dashboard',
  '/documents': 'Documents',
  '/documents/upload': 'Upload',
  '/review': 'Review Queue',
  '/materials': 'Materials',
  '/providers': 'Providers',
  '/destinations': 'Destinations',
  '/analytics': 'Analytics',
  '/users': 'Users',
};

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout, isAdmin } = useAuth();

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: user?.full_name || user?.username || 'Profile',
      disabled: true,
    },
    { type: 'divider' },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      onClick: handleLogout,
    },
  ];

  const pathParts = location.pathname.split('/').filter(Boolean);
  const breadcrumbItems = [
    { title: 'Home', onClick: () => navigate('/') },
    ...pathParts.map((part, index) => {
      const path = '/' + pathParts.slice(0, index + 1).join('/');
      const label = breadcrumbMap[path] || part;
      return { title: label };
    }),
  ];

  const selectedKeys = [location.pathname];
  const openKeys = location.pathname.startsWith('/documents') ? ['/documents'] : [];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          zIndex: 100,
        }}
        width={220}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '0 16px',
            borderBottom: '1px solid rgba(255,255,255,0.1)',
          }}
        >
          {!collapsed && (
            <Text
              strong
              style={{ color: 'white', fontSize: 16, whiteSpace: 'nowrap', overflow: 'hidden' }}
            >
              Invoice System
            </Text>
          )}
          {collapsed && (
            <Text strong style={{ color: 'white', fontSize: 16 }}>
              IS
            </Text>
          )}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={selectedKeys}
          defaultOpenKeys={openKeys}
          items={isAdmin ? adminMenuItems : menuItems}
          onClick={handleMenuClick}
          style={{ borderRight: 0 }}
        />
      </Sider>
      <Layout style={{ marginLeft: collapsed ? 80 : 220, transition: 'margin-left 0.2s' }}>
        <Header
          style={{
            padding: '0 24px',
            background: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid #f0f0f0',
            position: 'sticky',
            top: 0,
            zIndex: 99,
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
          }}
        >
          <Space>
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              style={{ fontSize: 16, width: 40, height: 40 }}
            />
          </Space>
          <Space>
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight" arrow>
              <Space style={{ cursor: 'pointer' }}>
                <Avatar
                  style={{ backgroundColor: '#1677ff' }}
                  icon={<UserOutlined />}
                  size="small"
                />
                {!collapsed && (
                  <Text>{user?.full_name || user?.username}</Text>
                )}
              </Space>
            </Dropdown>
          </Space>
        </Header>
        <Content style={{ margin: '16px 24px', overflow: 'initial' }}>
          <Breadcrumb
            items={breadcrumbItems}
            style={{ marginBottom: 16 }}
          />
          <div style={{ minHeight: 360 }}>
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  );
}
