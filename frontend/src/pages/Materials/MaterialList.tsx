import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Table,
  Button,
  Input,
  Select,
  Card,
  Typography,
  Tag,
  Modal,
  Form,
  message,
  Row,
  Col,
} from 'antd';
import { SearchOutlined, PlusOutlined, EyeOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { useMaterials, useCreateMaterial, useFamilies } from '../../hooks/useMaterials';
import type { MaterialMaster, ListParams, CreateMaterialRequest } from '../../types';

const { Title } = Typography;

export default function MaterialList() {
  const navigate = useNavigate();
  const [params, setParams] = useState<ListParams>({ page: 1, size: 20 });
  const [searchText, setSearchText] = useState('');
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [form] = Form.useForm();

  const { data, isLoading } = useMaterials(params);
  const { data: families } = useFamilies();
  const createMaterialMutation = useCreateMaterial();

  const familyOptions = [
    { value: '', label: 'Todas las familias' },
    ...(families || []).map((f) => ({ value: f.id, label: f.name })),
  ];

  const handleSearch = () => {
    setParams((prev) => ({ ...prev, search: searchText, page: 1 }));
  };

  const handleCreateMaterial = async () => {
    const values: CreateMaterialRequest = await form.validateFields();
    try {
      await createMaterialMutation.mutateAsync(values);
      message.success('Material created successfully');
      setCreateModalOpen(false);
      form.resetFields();
    } catch {
      message.error('Failed to create material');
    }
  };

  const columns: ColumnsType<MaterialMaster> = [
    {
      title: 'Código',
      dataIndex: 'master_code',
      key: 'master_code',
      width: 130,
      render: (code, record) => (
        <a onClick={() => navigate(`/materials/${record.id}`)}>{code}</a>
      ),
    },
    {
      title: 'Descripción',
      dataIndex: 'normalized_description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: 'Familia',
      key: 'family',
      width: 150,
      render: (_, r) =>
        r.family ? <Tag color="blue">{r.family.name}</Tag> : <Tag>Uncategorized</Tag>,
    },
    {
      title: 'Dimensiones',
      dataIndex: 'dimensions',
      key: 'dimensions',
      width: 120,
      render: (d) => d || '—',
    },
    {
      title: 'Unidad base',
      dataIndex: 'base_unit',
      key: 'base_unit',
      width: 100,
      align: 'center',
    },
    {
      title: 'Alias',
      dataIndex: 'aliases_count',
      key: 'aliases_count',
      width: 80,
      align: 'center',
      render: (count) => (
        <Tag color={count > 0 ? 'green' : 'default'}>{count}</Tag>
      ),
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
      title: 'Acciones',
      key: 'actions',
      width: 80,
      render: (_, record) => (
        <Button
          type="text"
          icon={<EyeOutlined />}
          onClick={() => navigate(`/materials/${record.id}`)}
          title="View"
        />
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>
          Catálogo de materiales
        </Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setCreateModalOpen(true)}
        >
          Nuevo material
        </Button>
      </div>

      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[12, 12]} align="middle">
          <Col xs={24} sm={12} md={8}>
            <Input
              placeholder="Buscar materiales..."
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onPressEnter={handleSearch}
              allowClear
            />
          </Col>
          <Col xs={24} sm={8} md={6}>
            <Select
              style={{ width: '100%' }}
              options={familyOptions}
              defaultValue=""
              onChange={(value: number | '') =>
                setParams((prev) => ({
                  ...prev,
                  family_id: value !== '' ? (value as number) : undefined,
                  page: 1,
                }))
              }
              placeholder="Filter by family"
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
            showTotal: (total) => `Total ${total} materials`,
            onChange: (page, pageSize) =>
              setParams((prev) => ({ ...prev, page, size: pageSize })),
          }}
        />
      </Card>

      <Modal
        title="Create Nuevo material"
        open={createModalOpen}
        onCancel={() => {
          setCreateModalOpen(false);
          form.resetFields();
        }}
        onOk={handleCreateMaterial}
        confirmLoading={createMaterialMutation.isPending}
        okText="Create"
        width={600}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="master_code"
                label="Master Code"
                rules={[{ required: true, message: 'Code is required' }]}
              >
                <Input placeholder="e.g. MAT-001" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="family_id" label="Family">
                <Select
                  options={(families || []).map((f) => ({ value: f.id, label: f.name }))}
                  placeholder="Select family"
                  allowClear
                />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item
            name="normalized_description"
            label="Description"
            rules={[{ required: true, message: 'Description is required' }]}
          >
            <Input placeholder="Normalized material description" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="dimensions" label="Dimensions">
                <Input placeholder="e.g. 100x200mm" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="base_unit"
                label="Base Unit"
                rules={[{ required: true, message: 'Unit is required' }]}
              >
                <Input placeholder="e.g. UN, KG, M2" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  );
}
