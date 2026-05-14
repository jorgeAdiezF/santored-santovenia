import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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
  Popconfirm,
  Row,
  Col,
  Switch,
} from 'antd';
import { SearchOutlined, PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import {
  listDestinations,
  createDestination,
  updateDestination,
  deleteDestination,
} from '../../api/destinations';
import type { Destination, CreateDestinationRequest } from '../../types';

const { Title } = Typography;
const { TextArea } = Input;

export default function DestinationList() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(20);
  const [searchText, setSearchText] = useState('');
  const [search, setSearch] = useState('');
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editDestination, setEditDestination] = useState<Destination | null>(null);
  const [form] = Form.useForm();

  const { data, isLoading } = useQuery({
    queryKey: ['destinations', page, size, search],
    queryFn: () => listDestinations({ page, size, search }),
  });

  const createMutation = useMutation({
    mutationFn: (data: CreateDestinationRequest) => createDestination(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['destinations'] });
      message.success('Destination created');
      setCreateModalOpen(false);
      form.resetFields();
    },
    onError: () => message.error('Failed to create destination'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<CreateDestinationRequest> }) =>
      updateDestination(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['destinations'] });
      message.success('Destination updated');
      setEditDestination(null);
      form.resetFields();
    },
    onError: () => message.error('Failed to update destination'),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteDestination,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['destinations'] });
      message.success('Destination deleted');
    },
    onError: () => message.error('Failed to delete destination'),
  });

  const handleCreate = async () => {
    const values = await form.validateFields();
    createMutation.mutate(values);
  };

  const handleUpdate = async () => {
    const values = await form.validateFields();
    updateMutation.mutate({ id: editDestination!.id, data: values });
  };

  const openEdit = (destination: Destination) => {
    setEditDestination(destination);
    form.setFieldsValue(destination);
  };

  const columns: ColumnsType<Destination> = [
    {
      title: 'Código',
      dataIndex: 'code',
      key: 'code',
      width: 120,
      render: (code) => <Tag color="blue">{code}</Tag>,
    },
    {
      title: 'Nombre',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
    },
    {
      title: 'Descripción',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (d) => d || '—',
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
      title: 'Created',
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
            icon={<EditOutlined />}
            onClick={() => openEdit(record)}
            title="Edit"
          />
          <Popconfirm
            title="Delete Destination"
            description="Are you sure you want to delete this destination?"
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

  const DestinationForm = () => (
    <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
      <Row gutter={16}>
        <Col span={8}>
          <Form.Item name="code" label="Code" rules={[{ required: true, message: 'Code is required' }]}>
            <Input placeholder="e.g. DEST-001" />
          </Form.Item>
        </Col>
        <Col span={16}>
          <Form.Item name="name" label="Name" rules={[{ required: true, message: 'Name is required' }]}>
            <Input placeholder="Destination name" />
          </Form.Item>
        </Col>
      </Row>
      <Form.Item name="description" label="Description">
        <TextArea rows={3} placeholder="Optional description" />
      </Form.Item>
      {editDestination && (
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
          Destinations
        </Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            form.resetFields();
            setCreateModalOpen(true);
          }}
        >
          Nuevo destino
        </Button>
      </div>

      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[12, 12]} align="middle">
          <Col xs={24} sm={16} md={10}>
            <Input
              placeholder="Search destinations..."
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onPressEnter={() => { setSearch(searchText); setPage(1); }}
              allowClear
              onClear={() => { setSearch(''); setPage(1); }}
            />
          </Col>
          <Col>
            <Button
              type="primary"
              icon={<SearchOutlined />}
              onClick={() => { setSearch(searchText); setPage(1); }}
            >
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
            current: page,
            pageSize: size,
            total: data?.total || 0,
            showSizeChanger: true,
            showTotal: (total) => `Total ${total} destinations`,
            onChange: (p, s) => { setPage(p); setSize(s); },
          }}
        />
      </Card>

      <Modal
        title="Create Nuevo destino"
        open={createModalOpen}
        onCancel={() => { setCreateModalOpen(false); form.resetFields(); }}
        onOk={handleCreate}
        confirmLoading={createMutation.isPending}
        okText="Create"
      >
        <DestinationForm />
      </Modal>

      <Modal
        title="Edit Destination"
        open={!!editDestination}
        onCancel={() => { setEditDestination(null); form.resetFields(); }}
        onOk={handleUpdate}
        confirmLoading={updateMutation.isPending}
        okText="Save"
      >
        <DestinationForm />
      </Modal>
    </div>
  );
}
