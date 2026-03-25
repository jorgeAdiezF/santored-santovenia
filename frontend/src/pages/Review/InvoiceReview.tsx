import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Form,
  Input,
  InputNumber,
  DatePicker,
  Button,
  Table,
  Tag,
  Space,
  Typography,
  Spin,
  Alert,
  Modal,
  Select,
  message,
  Row,
  Col,
  Descriptions,
  Tooltip,
  Badge,
} from 'antd';
import {
  ArrowLeftOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  EditOutlined,
  EnvironmentOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import {
  useInvoice,
  useUpdateInvoiceHeader,
  useUpdateInvoiceLine,
  useFinalizeInvoice,
  useRejectInvoice,
  useHomologateLine,
} from '../../hooks/useReview';
import { useMaterials, useProviders } from '../../hooks/useMaterials';
import { listDestinations } from '../../api/destinations';
import { assignDestination } from '../../api/destinations';
import type { InvoiceLine, LineStatus } from '../../types';

const { Title, Text } = Typography;
const { TextArea } = Input;

const lineStatusColors: Record<LineStatus, string> = {
  pending: 'default',
  homologated: 'success',
  manual: 'blue',
  rejected: 'error',
};

function ConfidenceBadge({ value }: { value: number }) {
  const pct = (value * 100).toFixed(0);
  const color = value >= 0.9 ? '#52c41a' : value >= 0.7 ? '#fa8c16' : '#f5222d';
  return (
    <Text strong style={{ color }}>
      {pct}%
    </Text>
  );
}

interface EditLineModalProps {
  open: boolean;
  line: InvoiceLine | null;
  invoiceId: number;
  onClose: () => void;
}

function EditLineModal({ open, line, invoiceId, onClose }: EditLineModalProps) {
  const [form] = Form.useForm();
  const updateLineMutation = useUpdateInvoiceLine();

  const handleSave = async () => {
    const values = await form.validateFields();
    try {
      await updateLineMutation.mutateAsync({
        invoiceId,
        lineId: line!.id,
        data: values,
      });
      message.success('Line updated');
      onClose();
    } catch {
      message.error('Failed to update line');
    }
  };

  return (
    <Modal
      title={`Edit Line #${line?.line_number}`}
      open={open}
      onCancel={onClose}
      onOk={handleSave}
      confirmLoading={updateLineMutation.isPending}
      width={600}
    >
      {line && (
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            supplier_code: line.supplier_code,
            description: line.description,
            quantity: line.quantity,
            unit: line.unit,
            unit_price: line.unit_price,
            discount: line.discount,
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="supplier_code" label="Supplier Code">
                <Input />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="unit" label="Unit">
                <Input />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="description" label="Description" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="quantity" label="Quantity" rules={[{ required: true }]}>
                <InputNumber style={{ width: '100%' }} min={0} step={0.001} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="unit_price" label="Unit Price" rules={[{ required: true }]}>
                <InputNumber style={{ width: '100%' }} min={0} step={0.01} precision={2} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="discount" label="Discount (%)">
                <InputNumber style={{ width: '100%' }} min={0} max={100} step={0.01} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      )}
    </Modal>
  );
}

interface HomologateModalProps {
  open: boolean;
  line: InvoiceLine | null;
  invoiceId: number;
  onClose: () => void;
}

function HomologateModal({ open, line, invoiceId, onClose }: HomologateModalProps) {
  const [selectedMaterial, setSelectedMaterial] = useState<number | null>(null);
  const [search, setSearch] = useState('');
  const { data: materialsData } = useMaterials({ search, size: 20 });
  const homologateMutation = useHomologateLine();

  const handleHomologate = async () => {
    if (!selectedMaterial) {
      message.warning('Please select a material');
      return;
    }
    try {
      await homologateMutation.mutateAsync({
        invoiceId,
        lineId: line!.id,
        data: { material_id: selectedMaterial, confirmed: true },
      });
      message.success('Line homologated successfully');
      onClose();
    } catch {
      message.error('Failed to homologate line');
    }
  };

  return (
    <Modal
      title={`Homologate Line #${line?.line_number}`}
      open={open}
      onCancel={onClose}
      onOk={handleHomologate}
      confirmLoading={homologateMutation.isPending}
      okText="Homologate"
    >
      {line && (
        <Space direction="vertical" style={{ width: '100%' }}>
          <Descriptions size="small" column={1}>
            <Descriptions.Item label="Description">{line.description}</Descriptions.Item>
            <Descriptions.Item label="Supplier Code">{line.supplier_code || '—'}</Descriptions.Item>
          </Descriptions>
          <Select
            showSearch
            style={{ width: '100%' }}
            placeholder="Search and select material master..."
            filterOption={false}
            onSearch={(val) => setSearch(val)}
            onChange={(val) => setSelectedMaterial(val as number)}
            options={(materialsData?.items || []).map((m) => ({
              value: m.id,
              label: `[${m.master_code}] ${m.normalized_description}`,
            }))}
            value={selectedMaterial}
            notFoundContent="No materials found"
          />
        </Space>
      )}
    </Modal>
  );
}

interface AssignDestinationModalProps {
  open: boolean;
  line: InvoiceLine | null;
  invoiceId: number;
  onClose: () => void;
}

function AssignDestinationModal({ open, line, invoiceId, onClose }: AssignDestinationModalProps) {
  const [form] = Form.useForm();
  const [destinations, setDestinations] = useState<{ value: number; label: string }[]>([]);
  const [loadingDest, setLoadingDest] = useState(false);

  const loadDestinations = async (search?: string) => {
    setLoadingDest(true);
    try {
      const result = await listDestinations({ search, size: 50 });
      setDestinations(result.items.map((d) => ({ value: d.id, label: `[${d.code}] ${d.name}` })));
    } finally {
      setLoadingDest(false);
    }
  };

  const handleAssign = async () => {
    const values = await form.validateFields();
    try {
      await assignDestination(invoiceId, {
        line_id: line!.id,
        destination_id: values.destination_id,
        quantity: values.quantity,
      });
      message.success('Destination assigned');
      onClose();
    } catch {
      message.error('Failed to assign destination');
    }
  };

  return (
    <Modal
      title={`Assign Destination - Line #${line?.line_number}`}
      open={open}
      onCancel={onClose}
      onOk={handleAssign}
      okText="Assign"
      afterOpenChange={(v) => v && loadDestinations()}
    >
      {line && (
        <Form form={form} layout="vertical" initialValues={{ quantity: line.quantity }}>
          <Descriptions size="small" column={1} style={{ marginBottom: 16 }}>
            <Descriptions.Item label="Description">{line.description}</Descriptions.Item>
            <Descriptions.Item label="Total Qty">{line.quantity} {line.unit}</Descriptions.Item>
          </Descriptions>
          <Form.Item name="destination_id" label="Destination" rules={[{ required: true }]}>
            <Select
              showSearch
              options={destinations}
              loading={loadingDest}
              filterOption={false}
              onSearch={loadDestinations}
              placeholder="Select destination"
              notFoundContent="No destinations found"
            />
          </Form.Item>
          <Form.Item name="quantity" label="Quantity" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} min={0} step={0.001} max={line.quantity} />
          </Form.Item>
        </Form>
      )}
    </Modal>
  );
}

export default function InvoiceReview() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const invoiceId = parseInt(id || '0', 10);

  const { data: invoice, isLoading, error } = useInvoice(invoiceId);
  const [form] = Form.useForm();
  const [editingHeader, setEditingHeader] = useState(false);
  const [editLine, setEditLine] = useState<InvoiceLine | null>(null);
  const [homologateLine, setHomologateLine] = useState<InvoiceLine | null>(null);
  const [assignLine, setAssignLine] = useState<InvoiceLine | null>(null);
  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState('');

  const updateHeaderMutation = useUpdateInvoiceHeader();
  const finalizeInvoiceMutation = useFinalizeInvoice();
  const rejectInvoiceMutation = useRejectInvoice();
  const { data: providersData } = useProviders({ size: 200 });

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (error || !invoice) {
    return (
      <Alert
        message="Invoice Not Found"
        type="error"
        showIcon
        action={<Button onClick={() => navigate('/review')}>Back to Queue</Button>}
      />
    );
  }

  const handleSaveHeader = async () => {
    const values = await form.validateFields();
    try {
      await updateHeaderMutation.mutateAsync({
        id: invoiceId,
        data: {
          ...values,
          invoice_date: values.invoice_date?.format('YYYY-MM-DD'),
          due_date: values.due_date?.format('YYYY-MM-DD'),
        },
      });
      message.success('Invoice header updated');
      setEditingHeader(false);
    } catch {
      message.error('Failed to update invoice');
    }
  };

  const handleFinalize = async () => {
    try {
      await finalizeInvoiceMutation.mutateAsync(invoiceId);
      message.success('Invoice approved successfully');
      navigate('/review');
    } catch {
      message.error('Failed to approve invoice');
    }
  };

  const handleReject = async () => {
    if (!rejectReason.trim()) {
      message.warning('Please provide a rejection reason');
      return;
    }
    try {
      await rejectInvoiceMutation.mutateAsync({ id: invoiceId, reason: rejectReason });
      message.success('Invoice rejected');
      navigate('/review');
    } catch {
      message.error('Failed to reject invoice');
    }
  };

  const isReadOnly = invoice.status === 'approved' || invoice.status === 'rejected' || invoice.status === 'exported';

  const lineColumns: ColumnsType<InvoiceLine> = [
    {
      title: '#',
      dataIndex: 'line_number',
      key: 'line_number',
      width: 50,
    },
    {
      title: 'Code',
      dataIndex: 'supplier_code',
      key: 'supplier_code',
      width: 100,
      render: (c) => c || '—',
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: 'Qty',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 80,
      align: 'right',
    },
    {
      title: 'Unit',
      dataIndex: 'unit',
      key: 'unit',
      width: 60,
    },
    {
      title: 'Price',
      dataIndex: 'unit_price',
      key: 'unit_price',
      width: 100,
      align: 'right',
      render: (v) => `€${(v || 0).toFixed(2)}`,
    },
    {
      title: 'Disc%',
      dataIndex: 'discount',
      key: 'discount',
      width: 70,
      align: 'right',
      render: (v) => (v ? `${v}%` : '—'),
    },
    {
      title: 'Subtotal',
      dataIndex: 'subtotal',
      key: 'subtotal',
      width: 110,
      align: 'right',
      render: (v) => `€${(v || 0).toFixed(2)}`,
    },
    {
      title: 'Conf.',
      dataIndex: 'confidence',
      key: 'confidence',
      width: 70,
      render: (c) => <ConfidenceBadge value={c || 0} />,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 110,
      render: (status: LineStatus) => (
        <Tag color={lineStatusColors[status]}>{status.replace(/_/g, ' ').toUpperCase()}</Tag>
      ),
    },
    {
      title: 'Material',
      key: 'material',
      width: 120,
      render: (_, r) =>
        r.material ? (
          <Tooltip title={r.material.normalized_description}>
            <Tag color="blue">{r.material.master_code}</Tag>
          </Tooltip>
        ) : (
          <Badge status="warning" text="Not mapped" />
        ),
    },
    {
      title: 'Dest.',
      key: 'destinations',
      width: 70,
      render: (_, r) =>
        r.destinations?.length > 0 ? (
          <Badge count={r.destinations.length} color="green" />
        ) : (
          <Badge status="default" text="None" />
        ),
    },
    ...(isReadOnly
      ? []
      : [
          {
            title: 'Actions',
            key: 'actions',
            width: 130,
            render: (_: unknown, record: InvoiceLine) => (
              <Space size={4}>
                <Tooltip title="Edit line">
                  <Button
                    type="text"
                    size="small"
                    icon={<EditOutlined />}
                    onClick={() => setEditLine(record)}
                  />
                </Tooltip>
                <Tooltip title="Homologate">
                  <Button
                    type="text"
                    size="small"
                    icon={<CheckCircleOutlined />}
                    onClick={() => setHomologateLine(record)}
                    style={{ color: record.status === 'homologated' ? '#52c41a' : undefined }}
                  />
                </Tooltip>
                <Tooltip title="Assign destination">
                  <Button
                    type="text"
                    size="small"
                    icon={<EnvironmentOutlined />}
                    onClick={() => setAssignLine(record)}
                  />
                </Tooltip>
              </Space>
            ),
          },
        ]),
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/review')}>
          Back to Queue
        </Button>
        <Title level={3} style={{ margin: 0 }}>
          Invoice Review — {invoice.invoice_number || `#${invoice.id}`}
        </Title>
        <Tag
          color={
            invoice.status === 'approved'
              ? 'success'
              : invoice.status === 'rejected'
              ? 'error'
              : invoice.status === 'pending_review'
              ? 'orange'
              : 'blue'
          }
        >
          {invoice.status.replace(/_/g, ' ').toUpperCase()}
        </Tag>
      </Space>

      <Row gutter={[16, 16]}>
        <Col xs={24}>
          <Card
            title="Invoice Header"
            extra={
              !isReadOnly && (
                editingHeader ? (
                  <Space>
                    <Button onClick={() => setEditingHeader(false)}>Cancel</Button>
                    <Button
                      type="primary"
                      onClick={handleSaveHeader}
                      loading={updateHeaderMutation.isPending}
                    >
                      Save
                    </Button>
                  </Space>
                ) : (
                  <Button icon={<EditOutlined />} onClick={() => {
                    setEditingHeader(true);
                    form.setFieldsValue({
                      provider_id: invoice.provider_id,
                      invoice_number: invoice.invoice_number,
                      invoice_date: invoice.invoice_date ? dayjs(invoice.invoice_date) : null,
                      due_date: invoice.due_date ? dayjs(invoice.due_date) : null,
                      subtotal: invoice.subtotal,
                      vat_amount: invoice.vat_amount,
                      total: invoice.total,
                      currency: invoice.currency,
                    });
                  }}>
                    Edit
                  </Button>
                )
              )
            }
          >
            {editingHeader ? (
              <Form form={form} layout="vertical">
                <Row gutter={16}>
                  <Col xs={24} sm={12} md={8}>
                    <Form.Item name="provider_id" label="Provider">
                      <Select
                        showSearch
                        options={(providersData?.items || []).map((p) => ({
                          value: p.id,
                          label: p.name,
                        }))}
                        placeholder="Select provider"
                        filterOption={(input, opt) =>
                          (opt?.label as string)?.toLowerCase().includes(input.toLowerCase())
                        }
                      />
                    </Form.Item>
                  </Col>
                  <Col xs={24} sm={12} md={8}>
                    <Form.Item name="invoice_number" label="Invoice Number">
                      <Input />
                    </Form.Item>
                  </Col>
                  <Col xs={24} sm={12} md={4}>
                    <Form.Item name="invoice_date" label="Invoice Date">
                      <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" />
                    </Form.Item>
                  </Col>
                  <Col xs={24} sm={12} md={4}>
                    <Form.Item name="due_date" label="Due Date">
                      <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" />
                    </Form.Item>
                  </Col>
                </Row>
                <Row gutter={16}>
                  <Col xs={24} sm={8} md={6}>
                    <Form.Item name="subtotal" label="Subtotal">
                      <InputNumber style={{ width: '100%' }} min={0} step={0.01} precision={2} prefix="€" />
                    </Form.Item>
                  </Col>
                  <Col xs={24} sm={8} md={6}>
                    <Form.Item name="vat_amount" label="VAT Amount">
                      <InputNumber style={{ width: '100%' }} min={0} step={0.01} precision={2} prefix="€" />
                    </Form.Item>
                  </Col>
                  <Col xs={24} sm={8} md={6}>
                    <Form.Item name="total" label="Total">
                      <InputNumber style={{ width: '100%' }} min={0} step={0.01} precision={2} prefix="€" />
                    </Form.Item>
                  </Col>
                  <Col xs={24} sm={8} md={6}>
                    <Form.Item name="currency" label="Currency">
                      <Input maxLength={3} />
                    </Form.Item>
                  </Col>
                </Row>
              </Form>
            ) : (
              <Descriptions column={{ xs: 1, sm: 2, md: 4 }}>
                <Descriptions.Item label="Provider">
                  {invoice.provider?.name || <Tag>Unknown</Tag>}
                </Descriptions.Item>
                <Descriptions.Item label="Invoice Number">
                  {invoice.invoice_number || '—'}
                </Descriptions.Item>
                <Descriptions.Item label="Invoice Date">
                  {invoice.invoice_date ? dayjs(invoice.invoice_date).format('DD/MM/YYYY') : '—'}
                </Descriptions.Item>
                <Descriptions.Item label="Due Date">
                  {invoice.due_date ? dayjs(invoice.due_date).format('DD/MM/YYYY') : '—'}
                </Descriptions.Item>
                <Descriptions.Item label="Subtotal">
                  €{(invoice.subtotal || 0).toLocaleString('es-ES', { minimumFractionDigits: 2 })}
                </Descriptions.Item>
                <Descriptions.Item label="VAT">
                  €{(invoice.vat_amount || 0).toLocaleString('es-ES', { minimumFractionDigits: 2 })}
                </Descriptions.Item>
                <Descriptions.Item label="Total">
                  <Text strong style={{ fontSize: 16 }}>
                    €{(invoice.total || 0).toLocaleString('es-ES', { minimumFractionDigits: 2 })}
                  </Text>
                </Descriptions.Item>
                <Descriptions.Item label="Currency">{invoice.currency || 'EUR'}</Descriptions.Item>
                <Descriptions.Item label="Confidence">
                  <ConfidenceBadge value={invoice.confidence || 0} />
                </Descriptions.Item>
              </Descriptions>
            )}
          </Card>
        </Col>

        <Col xs={24}>
          <Card title={`Invoice Lines (${invoice.lines?.length || 0})`}>
            <Table
              columns={lineColumns}
              dataSource={invoice.lines || []}
              rowKey="id"
              size="small"
              scroll={{ x: 1200 }}
              pagination={false}
              rowClassName={(record) => {
                if (record.confidence < 0.7) return 'row-low-confidence';
                if (record.confidence < 0.9) return 'row-medium-confidence';
                return '';
              }}
            />
          </Card>
        </Col>

        {!isReadOnly && (
          <Col xs={24}>
            <Card>
              <Space>
                <Button
                  type="primary"
                  icon={<CheckCircleOutlined />}
                  size="large"
                  onClick={handleFinalize}
                  loading={finalizeInvoiceMutation.isPending}
                >
                  Approve Invoice
                </Button>
                <Button
                  danger
                  icon={<CloseCircleOutlined />}
                  size="large"
                  onClick={() => setRejectModalOpen(true)}
                >
                  Reject Invoice
                </Button>
              </Space>
            </Card>
          </Col>
        )}
      </Row>

      <Modal
        title="Reject Invoice"
        open={rejectModalOpen}
        onCancel={() => setRejectModalOpen(false)}
        onOk={handleReject}
        okText="Reject"
        okButtonProps={{ danger: true }}
        confirmLoading={rejectInvoiceMutation.isPending}
      >
        <TextArea
          placeholder="Enter rejection reason..."
          rows={4}
          value={rejectReason}
          onChange={(e) => setRejectReason(e.target.value)}
        />
      </Modal>

      <EditLineModal
        open={!!editLine}
        line={editLine}
        invoiceId={invoiceId}
        onClose={() => setEditLine(null)}
      />

      <HomologateModal
        open={!!homologateLine}
        line={homologateLine}
        invoiceId={invoiceId}
        onClose={() => setHomologateLine(null)}
      />

      <AssignDestinationModal
        open={!!assignLine}
        line={assignLine}
        invoiceId={invoiceId}
        onClose={() => setAssignLine(null)}
      />
    </div>
  );
}
