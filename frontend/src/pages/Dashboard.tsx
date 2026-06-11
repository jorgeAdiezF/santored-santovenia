import { useNavigate } from 'react-router-dom';
import { Card, Row, Col, Table, Tag, Typography, Statistic, Spin, Alert } from 'antd';
import {
  FileTextOutlined,
  ClockCircleOutlined,
  EuroOutlined,
  QuestionCircleOutlined,
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import dayjs from 'dayjs';
import { useDashboard } from '../hooks/useAnalytics';
import type { DocumentListItem } from '../types';
import type { ColumnsType } from 'antd/es/table';

const { Title } = Typography;

const statusColors: Record<string, string> = {
  uploaded: 'default',
  processing: 'processing',
  segmented: 'blue',
  ocr_done: 'cyan',
  completed: 'success',
  error: 'error',
};

const statusLabels: Record<string, string> = {
  uploaded: 'Subido',
  processing: 'Procesando',
  segmented: 'Segmentado',
  ocr_done: 'OCR listo',
  completed: 'Completado',
  error: 'Error',
};

export default function Dashboard() {
  const navigate = useNavigate();
  const { data: dashboard, isLoading, error } = useDashboard();

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="Error al cargar el panel"
        description="No se pudieron obtener los datos. Comprueba que el servidor está en marcha."
        type="error"
        showIcon
      />
    );
  }

  const monthlyChartOption = {
    tooltip: {
      trigger: 'axis',
      formatter: (params: { name: string; value: number }[]) => {
        const p = params[0];
        return `${p.name}<br/>Total: €${p.value.toLocaleString('es-ES', { minimumFractionDigits: 2 })}`;
      },
    },
    xAxis: {
      type: 'category',
      data: dashboard?.invoices_by_month?.map((m) => m.month) || [],
      axisLabel: { rotate: 30 },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (v: number) => `€${(v / 1000).toFixed(0)}k`,
      },
    },
    series: [
      {
        data: dashboard?.invoices_by_month?.map((m) => m.total) || [],
        type: 'line',
        smooth: true,
        areaStyle: { opacity: 0.1 },
        lineStyle: { color: '#1677ff' },
        itemStyle: { color: '#1677ff' },
      },
    ],
    grid: { left: 60, right: 20, top: 20, bottom: 50 },
  };

  const providerPieOption = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: €{c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      type: 'scroll',
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['40%', '50%'],
        data:
          dashboard?.spending_by_provider?.map((p) => ({
            name: p.provider_name,
            value: p.total.toFixed(2),
          })) || [],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0,0,0,0.5)',
          },
        },
      },
    ],
  };

  const docColumns: ColumnsType<DocumentListItem> = [
    {
      title: 'Archivo',
      dataIndex: 'original_filename',
      key: 'filename',
      ellipsis: true,
      render: (text, record) => (
        <a onClick={() => navigate(`/documents/${record.id}`)}>{text}</a>
      ),
    },
    {
      title: 'Fecha de subida',
      dataIndex: 'upload_date',
      key: 'upload_date',
      render: (d) => dayjs(d).format('DD/MM/YYYY HH:mm'),
      width: 160,
    },
    {
      title: 'Páginas',
      dataIndex: 'page_count',
      key: 'page_count',
      width: 80,
      align: 'center',
    },
    {
      title: 'Estado',
      dataIndex: 'status',
      key: 'status',
      width: 130,
      render: (status) => (
        <Tag color={statusColors[status] || 'default'}>
          {statusLabels[status] || (status ? status.replace('_', ' ').toUpperCase() : '—')}
        </Tag>
      ),
    },
  ];

  return (
    <div>
      <Title level={3} style={{ marginBottom: 24 }}>
        Panel de control
      </Title>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total facturas"
              value={dashboard?.total_invoices || 0}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1677ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Pendientes de revisión"
              value={dashboard?.pending_review || 0}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Gasto este mes"
              value={dashboard?.total_spent_this_month || 0}
              precision={2}
              prefix={<EuroOutlined />}
              suffix="€"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Sin homologar"
              value={dashboard?.pending_homologation || 0}
              prefix={<QuestionCircleOutlined />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={14}>
          <Card title="Gasto mensual (últimos 6 meses)">
            <ReactECharts option={monthlyChartOption} style={{ height: 280 }} />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title="Gasto por proveedor">
            <ReactECharts option={providerPieOption} style={{ height: 280 }} />
          </Card>
        </Col>
      </Row>

      <Card title="Documentos recientes">
        <Table
          columns={docColumns}
          dataSource={dashboard?.recent_documents || []}
          rowKey="id"
          pagination={false}
          size="small"
          locale={{ emptyText: 'Sin documentos' }}
        />
      </Card>
    </div>
  );
}
