import { useState } from 'react';
import {
  Table,
  Button,
  Input,
  Card,
  Typography,
  Tag,
  Space,
  Modal,
  Form,
  message,
  Row,
  Col,
  Descriptions,
} from 'antd';
import { SearchOutlined, PlusOutlined, EditOutlined, EyeOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import { useProviders, useCreateProvider, useUpdateProvider } from '../../hooks/useMaterials';
import type { Provider, ListParams, CreateProviderRequest } from '../../types';

const { Title } = Typography;

export default function ProviderList() {
  const [params, setParams] = useState<ListParams>({ page: 1, size: 20 });
  const [searchText, setSearchText] = useState('');
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editProvider, setEditProvider] = useState<Provider | null>(null);
  const [viewProvider, setViewProvider] = useState<Provider | null>(null);
  const [form] = Form.useForm();

  const { data, isLoading } = useProviders(params);
  const createMutation = useCreateProvider();
  const updateMutation = useUpdateProvider();

  const handleSearch = () => {
    setParams((prev) => ({ ...prev, search: searchText, page: 1 }));
  };

  const handleCreate = async () => {
    const values: CreateProviderRequest = await form.validateFields();
    try {
      await createMutation.mutateAsync(values);
      message.success('Provider created');
      setCreateModalOpen(false);
      form.resetFields();
    } catch {
      message.error('Failed to create provider');
    }
  };

  const handleUpdate = async () => {
    const values = await form.validateFields();
    try {
      await updateMutation.mutateAsync({ id: editProvider!.id, data: values });
      message.success('Provider updated');
      setEditProvider(null);
      form.resetFields();
    } catch {
      message.error('Failed to update provider');
    }
  };

  const openEdit = (provider: Provider) => {
    setEditProvider(provider);
    form.setFieldsValue(provider);
  };

  const columns: ColumnsType<Provider> = [
    {
      title: 'Código',
      dataIndex: 'code',
      key: 'code',
      width: 100,
      render: (code, record) => (
        <a onClick={() => setViewProvider(record)}>{code}</a>
      ),
    },
    {
      title: 'Nombre',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
    },
    {
      title: 'NIF/CIF',
      dataIndex: 'tax_id',
      key: 'tax_id',
      width: 140,
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      ellipsis: true,
      render: (e) => e || '—',
    },
    {
      title: 'Teléfono',
      dataIndex: 'phone',
      key: 'phone',
      width: 140,
      render: (p) => p || '—',
    },
    {
      title: 'Alias',
      key: 'aliases',
      width: 80,
      align: 'center',
      render: (_, r) => <Tag color="blue">{r.aliases?.length || 0}</Tag>,
    },
    {
      title: 'Estado',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 90,
      render: (active) => (
        <Tag color={active ? 'success' : 'error'}>{active ? 'Active' : 'Inactive'}</Tag>
      ),
    },
    {
      title: 'Alta',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (d) => dayjs(d).format('DD/MM/YYYY'),
    },
    {
      title: 'Acciones',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => setViewProvider(record)}
            title="View"
          />
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => openEdit(record)}
            title="Edit"
          />
        </Space>
      ),
    },
  ];

  const ProviderForm = () => (
    <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
      <Row gutter={16}>
        <Col span={12}>
          <Form.Item name="code" label="Code" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="tax_id" label="Tax ID" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
        </Col>
      </Row>
      <Form.Item name="name" label="Name" rules={[{ required: true }]}>
        <Input />
      </Form.Item>
      <Form.Item name="address" label="Address">
        <Input />
      </Form.Item>
      <Row gutter={16}>
        <Col span={12}>
          <Form.Item name="email" label="Email">
            <Input type="email" />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="phone" label="Phone">
            <Input />
          </Form.Item>
        </Col>
      </Row>
    </Form>
  );

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>
          Providers
        </Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            form.resetFields();
            setCreateModalOpen(true);
          }}
        >
          Nuevo proveedor
        </Button>
      </div>

      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[12, 12]} align="middle">
          <Col xs={24} sm={16} md={10}>
            <Input
              placeholder="Buscar proveedores..."
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onPressEnter={handleSearch}
              allowClear
            />
          </Col>
          <Col xs={24} sm={4} md={2}>
            <Button type="primary" onClick={handleSearch} icon={<SearchOutlined />}>
              Search
            </Button>
          </Col>
        </Row>
      </Card>

      <Card>
        <Table
          columns={columns}
          dataSource={data?.items || []}
          rowKey="id"
          loading={isLoading}
          pagination={{
            current: params.page,
            pageSize: params.size,
            total: data?.total || 0,
            showSizeChanger: true,
            showTotal: (total) => `Total ${total} providers`,
            onChange: (page, pageSize) =>
              setParams((prev) => ({ ...prev, page, size: pageSize })),
          }}
        />
      </Card>

      <Modal
        title="Create Nuevo proveedor"
        open={createModalOpen}
        onCancel={() => {
          setCreateModalOpen(false);
          form.resetFields();
        }}
        onOk={handleCreate}
        confirmLoading={createMutation.isPending}
        okText="Create"
        width={600}
      >
        <ProviderForm />
      </Modal>

      <Modal
        title="Edit Provider"
        open={!!editProvider}
        onCancel={() => {
          setEditProvider(null);
          form.resetFields();
        }}
        onOk={handleUpdate}
        confirmLoading={updateMutation.isPending}
        okText="Save"
        width={600}
      >
        <ProviderForm />
      </Modal>

      <Modal
        title={viewProvider?.name}
        open={!!viewProvider}
        onCancel={() => setViewProvider(null)}
        footer={[
          <Button key="close" onClick={() => setViewProvider(null)}>
            Close
          </Button>,
          <Button
            key="edit"
            type="primary"
            icon={<EditOutlined />}
            onClick={() => {
              setViewProvider(null);
              openEdit(viewProvider!);
            }}
          >
            Edit
          </Button>,
        ]}
        width={600}
      >
        {viewProvider && (
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="Code">{viewProvider.code}</Descriptions.Item>
            <Descriptions.Item label="Tax ID">{viewProvider.tax_id}</Descriptions.Item>
            <Descriptions.Item label="Name" span={2}>{viewProvider.name}</Descriptions.Item>
            <Descriptions.Item label="Address" span={2}>{viewProvider.address || '—'}</Descriptions.Item>
            <Descriptions.Item label="Email">{viewProvider.email || '—'}</Descriptions.Item>
            <Descriptions.Item label="Phone">{viewProvider.phone || '—'}</Descriptions.Item>
            <Descriptions.Item label="Status">
              <Tag color={viewProvider.is_active ? 'success' : 'error'}>
                {viewProvider.is_active ? 'Active' : 'Inactive'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Aliases">
              <Tag color="blue">{viewProvider.aliases?.length || 0}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Created">
              {dayjs(viewProvider.created_at).format('DD/MM/YYYY')}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
}
