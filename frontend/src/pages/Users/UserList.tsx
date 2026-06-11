import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Table,
  Button,
  Card,
  Typography,
  Tag,
  Space,
  Modal,
  Form,
  Input,
  Select,
  message,
  Popconfirm,
  Switch,
  Row,
  Col,
  Avatar,
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, UserOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import { listUsers, createUser, updateUser, deleteUser } from '../../api/auth';
import type { User, Role } from '../../types';

const { Title } = Typography;

const roleColors: Record<Role, string> = {
  admin: 'red',
  reviewer: 'blue',
  viewer: 'green',
};

const roleOptions = [
  { value: 'admin', label: 'Admin' },
  { value: 'reviewer', label: 'Reviewer' },
  { value: 'viewer', label: 'Viewer' },
];

export default function UserList() {
  const queryClient = useQueryClient();
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editUser, setEditUser] = useState<User | null>(null);
  const [form] = Form.useForm();

  const { data: users, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: listUsers,
  });

  const createMutation = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      message.success('User created');
      setCreateModalOpen(false);
      form.resetFields();
    },
    onError: () => message.error('Failed to create user'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<User> }) => updateUser(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      message.success('User updated');
      setEditUser(null);
      form.resetFields();
    },
    onError: () => message.error('Failed to update user'),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      message.success('User deleted');
    },
    onError: () => message.error('Failed to delete user'),
  });

  const handleCreate = async () => {
    const values = await form.validateFields();
    createMutation.mutate(values);
  };

  const handleUpdate = async () => {
    const values = await form.validateFields();
    const { password, ...rest } = values;
    const updateData = password ? values : rest;
    updateMutation.mutate({ id: editUser!.id, data: updateData });
  };

  const openEdit = (user: User) => {
    setEditUser(user);
    form.setFieldsValue({
      username: user.username,
      email: user.email,
      full_name: user.full_name,
      role: user.role,
      is_active: user.is_active,
    });
  };

  const columns: ColumnsType<User> = [
    {
      title: 'User',
      key: 'user',
      render: (_, record) => (
        <Space>
          <Avatar icon={<UserOutlined />} size="small" style={{ backgroundColor: '#1677ff' }} />
          <Space direction="vertical" size={0}>
            <Typography.Text strong>{record.full_name}</Typography.Text>
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              @{record.username}
            </Typography.Text>
          </Space>
        </Space>
      ),
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      ellipsis: true,
    },
    {
      title: 'Role',
      dataIndex: 'role',
      key: 'role',
      width: 100,
      render: (role: Role) => (
        <Tag color={roleColors[role]}>{role.toUpperCase()}</Tag>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 90,
      render: (active) => (
        <Tag color={active ? 'success' : 'error'}>{active ? 'Active' : 'Inactive'}</Tag>
      ),
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (d) => dayjs(d).format('DD/MM/YYYY'),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => openEdit(record)}
            title="Edit"
          />
          <Popconfirm
            title="Delete User"
            description={`Are you sure you want to delete "${record.username}"?`}
            onConfirm={() => deleteMutation.mutate(record.id)}
            okText="Delete"
            okButtonProps={{ danger: true }}
          >
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              loading={deleteMutation.isPending}
              title="Delete"
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const UserForm = ({ isEdit = false }: { isEdit?: boolean }) => (
    <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            name="username"
            label="Username"
            rules={[{ required: true, message: 'Username is required' }]}
          >
            <Input disabled={isEdit} />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name="role"
            label="Role"
            rules={[{ required: true, message: 'Role is required' }]}
          >
            <Select options={roleOptions} />
          </Form.Item>
        </Col>
      </Row>
      <Form.Item
        name="full_name"
        label="Full Name"
        rules={[{ required: true, message: 'Full name is required' }]}
      >
        <Input />
      </Form.Item>
      <Form.Item
        name="email"
        label="Email"
        rules={[
          { required: true, message: 'Email is required' },
          { type: 'email', message: 'Invalid email format' },
        ]}
      >
        <Input type="email" />
      </Form.Item>
      <Form.Item
        name="password"
        label={isEdit ? 'New Password (leave blank to keep current)' : 'Password'}
        rules={isEdit ? [] : [{ required: true, message: 'Password is required' }]}
      >
        <Input.Password placeholder={isEdit ? 'Leave blank to keep current password' : ''} />
      </Form.Item>
      {isEdit && (
        <Form.Item name="is_active" label="Active" valuePropName="checked">
          <Switch />
        </Form.Item>
      )}
    </Form>
  );

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>
          User Management
        </Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            form.resetFields();
            setCreateModalOpen(true);
          }}
        >
          New User
        </Button>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={users || []}
          rowKey="id"
          loading={isLoading}
          pagination={{ pageSize: 20 }}
        />
      </Card>

      <Modal
        title="Create New User"
        open={createModalOpen}
        onCancel={() => {
          setCreateModalOpen(false);
          form.resetFields();
        }}
        onOk={handleCreate}
        confirmLoading={createMutation.isPending}
        okText="Create User"
        width={600}
      >
        <UserForm />
      </Modal>

      <Modal
        title={`Edit User — ${editUser?.username}`}
        open={!!editUser}
        onCancel={() => {
          setEditUser(null);
          form.resetFields();
        }}
        onOk={handleUpdate}
        confirmLoading={updateMutation.isPending}
        okText="Save Changes"
        width={600}
      >
        <UserForm isEdit />
      </Modal>
    </div>
  );
}
