import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Form,
  Input,
  Button,
  Typography,
  Spin,
  Alert,
  Space,
  Table,
  Tag,
  Modal,
  Select,
  message,
  Row,
  Col,
  Descriptions,
  Divider,
} from 'antd';
import { ArrowLeftOutlined, PlusOutlined, EditOutlined, SaveOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import {
  useMaterial,
  useMaterialAliases,
  useUpdateMaterial,
  useAddAlias,
  useFamilies,
  useProviders,
} from '../../hooks/useMaterials';
import type { MaterialAlias, AddAliasRequest } from '../../types';

const { Title, Text } = Typography;

export default function MaterialDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const materialId = parseInt(id || '0', 10);

  const [editMode, setEditMode] = useState(false);
  const [addAliasOpen, setAddAliasOpen] = useState(false);
  const [editForm] = Form.useForm();
  const [aliasForm] = Form.useForm();

  const { data: material, isLoading, error } = useMaterial(materialId);
  const { data: aliases } = useMaterialAliases(materialId);
  const { data: families } = useFamilies();
  const { data: providersData } = useProviders({ size: 200 });
  const updateMutation = useUpdateMaterial();
  const addAliasMutation = useAddAlias();

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (error || !material) {
    return (
      <Alert
        message="Material Not Found"
        type="error"
        showIcon
        action={<Button onClick={() => navigate('/materials')}>Back to Materials</Button>}
      />
    );
  }

  const handleSave = async () => {
    const values = await editForm.validateFields();
    try {
      await updateMutation.mutateAsync({ id: materialId, data: values });
      message.success('Material updated');
      setEditMode(false);
    } catch {
      message.error('Failed to update material');
    }
  };

  const handleAddAlias = async () => {
    const values: AddAliasRequest = await aliasForm.validateFields();
    try {
      await addAliasMutation.mutateAsync({ materialId, data: values });
      message.success('Alias added');
      setAddAliasOpen(false);
      aliasForm.resetFields();
    } catch {
      message.error('Failed to add alias');
    }
  };

  const aliasColumns: ColumnsType<MaterialAlias> = [
    {
      title: 'Description',
      dataIndex: 'alias_description',
      key: 'alias_description',
      ellipsis: true,
    },
    {
      title: 'Supplier Code',
      dataIndex: 'supplier_code',
      key: 'supplier_code',
      render: (c) => c || '—',
    },
    {
      title: 'Provider',
      key: 'provider',
      render: (_, r) => {
        const provider = providersData?.items?.find((p) => p.id === r.provider_id);
        return provider ? <Tag color="blue">{provider.name}</Tag> : '—';
      },
    },
    {
      title: 'Source',
      dataIndex: 'source',
      key: 'source',
      render: (s) => <Tag>{s}</Tag>,
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (d) => dayjs(d).format('DD/MM/YYYY'),
      width: 120,
    },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/materials')}>
          Back
        </Button>
        <Title level={3} style={{ margin: 0 }}>
          {material.master_code}
        </Title>
        <Tag color={material.is_active ? 'success' : 'error'}>
          {material.is_active ? 'Active' : 'Inactive'}
        </Tag>
      </Space>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card
            title="Material Information"
            extra={
              editMode ? (
                <Space>
                  <Button onClick={() => setEditMode(false)}>Cancel</Button>
                  <Button
                    type="primary"
                    icon={<SaveOutlined />}
                    onClick={handleSave}
                    loading={updateMutation.isPending}
                  >
                    Save
                  </Button>
                </Space>
              ) : (
                <Button
                  icon={<EditOutlined />}
                  onClick={() => {
                    setEditMode(true);
                    editForm.setFieldsValue({
                      master_code: material.master_code,
                      family_id: material.family_id,
                      normalized_description: material.normalized_description,
                      dimensions: material.dimensions,
                      base_unit: material.base_unit,
                    });
                  }}
                >
                  Edit
                </Button>
              )
            }
          >
            {editMode ? (
              <Form form={editForm} layout="vertical">
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item
                      name="master_code"
                      label="Master Code"
                      rules={[{ required: true }]}
                    >
                      <Input />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="family_id" label="Family">
                      <Select
                        options={(families || []).map((f) => ({ value: f.id, label: f.name }))}
                        allowClear
                        placeholder="Select family"
                      />
                    </Form.Item>
                  </Col>
                </Row>
                <Form.Item
                  name="normalized_description"
                  label="Description"
                  rules={[{ required: true }]}
                >
                  <Input />
                </Form.Item>
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item name="dimensions" label="Dimensions">
                      <Input />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="base_unit" label="Base Unit" rules={[{ required: true }]}>
                      <Input />
                    </Form.Item>
                  </Col>
                </Row>
              </Form>
            ) : (
              <Descriptions column={{ xs: 1, sm: 2 }}>
                <Descriptions.Item label="Master Code">
                  <Text strong>{material.master_code}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="Family">
                  {material.family ? (
                    <Tag color="blue">{material.family.name}</Tag>
                  ) : (
                    <Text type="secondary">Uncategorized</Text>
                  )}
                </Descriptions.Item>
                <Descriptions.Item label="Description" span={2}>
                  {material.normalized_description}
                </Descriptions.Item>
                <Descriptions.Item label="Dimensions">
                  {material.dimensions || '—'}
                </Descriptions.Item>
                <Descriptions.Item label="Base Unit">{material.base_unit}</Descriptions.Item>
                <Descriptions.Item label="Created">
                  {dayjs(material.created_at).format('DD/MM/YYYY')}
                </Descriptions.Item>
                <Descriptions.Item label="Updated">
                  {dayjs(material.updated_at).format('DD/MM/YYYY')}
                </Descriptions.Item>
              </Descriptions>
            )}
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card title="Stats">
            <Descriptions column={1} size="small">
              <Descriptions.Item label="Total Aliases">
                <Tag color="blue">{material.aliases_count}</Tag>
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>
      </Row>

      <Divider />

      <Card
        title={`Aliases (${aliases?.length || 0})`}
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setAddAliasOpen(true)}
            size="small"
          >
            Add Alias
          </Button>
        }
      >
        <Table
          columns={aliasColumns}
          dataSource={aliases || []}
          rowKey="id"
          size="small"
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title="Add Material Alias"
        open={addAliasOpen}
        onCancel={() => {
          setAddAliasOpen(false);
          aliasForm.resetFields();
        }}
        onOk={handleAddAlias}
        confirmLoading={addAliasMutation.isPending}
        okText="Add Alias"
      >
        <Form form={aliasForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="alias_description"
            label="Alias Description"
            rules={[{ required: true, message: 'Description is required' }]}
          >
            <Input placeholder="Supplier description for this material" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="supplier_code" label="Supplier Code">
                <Input placeholder="Supplier's part number" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="provider_id" label="Provider">
                <Select
                  options={(providersData?.items || []).map((p) => ({
                    value: p.id,
                    label: p.name,
                  }))}
                  allowClear
                  placeholder="Select provider"
                  showSearch
                  filterOption={(input, opt) =>
                    (opt?.label as string)?.toLowerCase().includes(input.toLowerCase())
                  }
                />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item
            name="source"
            label="Source"
            rules={[{ required: true, message: 'Source is required' }]}
            initialValue="manual"
          >
            <Select
              options={[
                { value: 'manual', label: 'Manual' },
                { value: 'ocr', label: 'OCR' },
                { value: 'import', label: 'Import' },
              ]}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
