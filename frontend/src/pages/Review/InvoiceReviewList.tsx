import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Table,
  Button,
  Tag,
  Select,
  DatePicker,
  Card,
  Typography,
  Row,
  Col,
  Progress,
} from 'antd';
import { EyeOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import { usePendingInvoices } from '../../hooks/useReview';
import { useProviders } from '../../hooks/useMaterials';
import type { Invoice, InvoiceStatus, ListParams } from '../../types';

const { Title } = Typography;
const { RangePicker } = DatePicker;

const statusColors: Record<InvoiceStatus, string> = {
  pending_review: 'orange',
  under_review: 'blue',
  approved: 'success',
  rejected: 'error',
  exported: 'purple',
};

const statusOptions = [
  { value: '', label: 'Todos los estados' },
  { value: 'pending_review', label: 'Pending Review' },
  { value: 'under_review', label: 'Under Review' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'exported', label: 'Exported' },
];

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const status = value >= 0.9 ? 'success' : value >= 0.7 ? 'normal' : 'exception';
  return <Progress percent={pct} size="small" status={status} style={{ width: 80 }} />;
}

export default function InvoiceReviewList() {
  const navigate = useNavigate();
  const [params, setParams] = useState<ListParams>({ page: 1, size: 20 });

  const { data, isLoading } = usePendingInvoices(params);
  const { data: providersData } = useProviders({ size: 200 });

  const providerOptions = [
    { value: '', label: 'Todos los proveedores' },
    ...(providersData?.items || []).map((p) => ({ value: p.id, label: p.name })),
  ];

  const columns: ColumnsType<Invoice> = [
    {
      title: 'Nº factura',
      dataIndex: 'invoice_number',
      key: 'invoice_number',
      render: (num, record) => (
        <a onClick={() => navigate(`/review/${record.id}`)}>{num || `INV-${record.id}`}</a>
      ),
    },
    {
      title: 'Proveedor',
      key: 'provider',
      render: (_, record) => record.provider?.name || <Tag>Unknown</Tag>,
    },
    {
      title: 'Fecha',
      dataIndex: 'invoice_date',
      key: 'invoice_date',
      width: 130,
      render: (d) => (d ? dayjs(d).format('DD/MM/YYYY') : '—'),
    },
    {
      title: 'Total',
      dataIndex: 'total',
      key: 'total',
      width: 120,
      align: 'right',
      render: (v) =>
        v != null
          ? `€${v.toLocaleString('es-ES', { minimumFractionDigits: 2 })}`
          : '—',
    },
    {
      title: 'Líneas',
      key: 'lines',
      width: 70,
      align: 'center',
      render: (_, r) => r.lines?.length || 0,
    },
    {
      title: 'Confianza',
      dataIndex: 'confidence',
      key: 'confidence',
      width: 110,
      render: (c) => <ConfidenceBar value={c || 0} />,
    },
    {
      title: 'Estado',
      dataIndex: 'status',
      key: 'status',
      width: 140,
      render: (status: InvoiceStatus) => (
        <Tag color={statusColors[status] || 'default'}>
          {status.replace(/_/g, ' ').toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Acciones',
      key: 'actions',
      width: 80,
      render: (_, record) => (
        <Button
          type="primary"
          size="small"
          icon={<EyeOutlined />}
          onClick={() => navigate(`/review/${record.id}`)}
        >
          Review
        </Button>
      ),
    },
  ];

  return (
    <div>
      <Title level={3} style={{ marginBottom: 16 }}>
        Cola de revisión
      </Title>

      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[12, 12]} align="middle">
          <Col xs={24} sm={8} md={6}>
            <Select
              style={{ width: '100%' }}
              options={providerOptions}
              defaultValue=""
              onChange={(value: number | '') =>
                setParams((prev) => ({
                  ...prev,
                  provider_id: value !== '' ? (value as number) : undefined,
                  page: 1,
                }))
              }
              placeholder="Filter by provider"
            />
          </Col>
          <Col xs={24} sm={8} md={6}>
            <Select
              style={{ width: '100%' }}
              options={statusOptions}
              defaultValue=""
              onChange={(value) =>
                setParams((prev) => ({ ...prev, status: value || undefined, page: 1 }))
              }
              placeholder="Filter by status"
            />
          </Col>
          <Col xs={24} sm={12} md={8}>
            <RangePicker
              style={{ width: '100%' }}
              onChange={(dates) => {
                setParams((prev) => ({
                  ...prev,
                  date_from: dates?.[0]?.format('YYYY-MM-DD'),
                  date_to: dates?.[1]?.format('YYYY-MM-DD'),
                  page: 1,
                }));
              }}
            />
          </Col>
        </Row>
      </Card>

      <Card>
        <Table
          columns={columns}
          dataSource={Array.isArray(data) ? data : []}
          rowKey="id"
          loading={isLoading}
          pagination={{
            current: params.page,
            pageSize: params.size,
            total: Array.isArray(data) ? data.length : 0,
            showSizeChanger: true,
            showTotal: (total) => `Total ${total} invoices`,
            onChange: (page, pageSize) =>
              setParams((prev) => ({ ...prev, page, size: pageSize })),
          }}
          onRow={(_record) => ({
            style: { cursor: 'pointer' },
          })}
        />
      </Card>
    </div>
  );
}
