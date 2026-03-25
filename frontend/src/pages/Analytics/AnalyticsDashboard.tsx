import { useState } from 'react';
import {
  Card,
  Row,
  Col,
  Select,
  DatePicker,
  Typography,
  Spin,
  Space,
  Table,
  Tag,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import ReactECharts from 'echarts-for-react';
import dayjs from 'dayjs';
import {
  usePriceHistory,
  useMaterialsStats,
  useProviderComparison,
  useSpendingByFamily,
} from '../../hooks/useAnalytics';
import { useMaterials } from '../../hooks/useMaterials';
import type { MaterialStats } from '../../types';

const { Title } = Typography;
const { RangePicker } = DatePicker;

export default function AnalyticsDashboard() {
  const [selectedMaterialId, setSelectedMaterialId] = useState<number | null>(null);
  const [materialSearch, setMaterialSearch] = useState('');
  const [dateRange, setDateRange] = useState<{ date_from?: string; date_to?: string }>({});

  const { data: materialsData } = useMaterials({ search: materialSearch, size: 30 });

  const { data: priceHistory, isLoading: loadingHistory } = usePriceHistory(
    selectedMaterialId || 0,
    dateRange
  );

  const { data: providerComparison, isLoading: loadingComparison } = useProviderComparison(
    selectedMaterialId || 0,
    dateRange
  );

  const { data: materialsStats, isLoading: loadingStats } = useMaterialsStats({
    ...dateRange,
    limit: 20,
  });

  const { data: spendingByFamily } = useSpendingByFamily(dateRange);

  const priceHistoryOption = {
    tooltip: {
      trigger: 'axis',
      formatter: (params: { seriesName: string; name: string; value: number }[]) => {
        return params
          .map((p) => `${p.seriesName}: €${p.value.toFixed(2)}`)
          .join('<br/>');
      },
    },
    legend: { type: 'scroll' },
    xAxis: {
      type: 'time',
      axisLabel: { formatter: (v: number) => dayjs(v).format('DD/MM/YY') },
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: (v: number) => `€${v.toFixed(2)}` },
    },
    series: (() => {
      if (!priceHistory) return [];
      const providerGroups: Record<string, { date: string; price: number }[]> = {};
      priceHistory.forEach((point) => {
        if (!providerGroups[point.provider_name]) {
          providerGroups[point.provider_name] = [];
        }
        providerGroups[point.provider_name].push({ date: point.date, price: point.price });
      });
      return Object.entries(providerGroups).map(([name, points]) => ({
        name,
        type: 'line',
        data: points.map((p) => [p.date, p.price]),
        smooth: true,
      }));
    })(),
    grid: { left: 60, right: 20, top: 40, bottom: 50 },
  };

  const providerComparisonOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    },
    xAxis: {
      type: 'category',
      data: providerComparison?.map((p) => p.provider_name) || [],
      axisLabel: { rotate: 30 },
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: (v: number) => `€${v.toFixed(2)}` },
    },
    series: [
      {
        name: 'Avg Price',
        type: 'bar',
        data: providerComparison?.map((p) => p.avg_price) || [],
        itemStyle: { color: '#1677ff' },
      },
      {
        name: 'Min Price',
        type: 'bar',
        data: providerComparison?.map((p) => p.min_price) || [],
        itemStyle: { color: '#52c41a' },
      },
      {
        name: 'Max Price',
        type: 'bar',
        data: providerComparison?.map((p) => p.max_price) || [],
        itemStyle: { color: '#f5222d' },
      },
    ],
    grid: { left: 60, right: 20, top: 40, bottom: 70 },
    legend: { top: 'top' },
  };

  const topMaterialsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: { name: string; value: number }[]) => {
        const p = params[0];
        return `${p.name}<br/>€${p.value.toLocaleString('es-ES', { minimumFractionDigits: 2 })}`;
      },
    },
    xAxis: {
      type: 'value',
      axisLabel: { formatter: (v: number) => `€${(v / 1000).toFixed(0)}k` },
    },
    yAxis: {
      type: 'category',
      data: [...(materialsStats || [])].reverse().map((m) => m.master_code),
      axisLabel: { width: 80, overflow: 'truncate' as const },
    },
    series: [
      {
        type: 'bar',
        data: [...(materialsStats || [])].reverse().map((m) => m.total_spend),
        itemStyle: { color: '#722ed1' },
      },
    ],
    grid: { left: 90, right: 40, top: 20, bottom: 30 },
  };

  const familyPieOption = {
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
        data: (spendingByFamily || []).map((f) => ({
          name: f.family_name,
          value: f.total.toFixed(2),
        })),
      },
    ],
  };

  const statsColumns: ColumnsType<MaterialStats> = [
    {
      title: 'Code',
      dataIndex: 'master_code',
      key: 'master_code',
      width: 120,
    },
    {
      title: 'Description',
      dataIndex: 'normalized_description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: 'Total Spend',
      dataIndex: 'total_spend',
      key: 'total_spend',
      align: 'right',
      render: (v) => `€${v.toLocaleString('es-ES', { minimumFractionDigits: 2 })}`,
      sorter: (a, b) => a.total_spend - b.total_spend,
      defaultSortOrder: 'descend',
    },
    {
      title: 'Qty',
      dataIndex: 'total_quantity',
      key: 'total_quantity',
      align: 'right',
      render: (v) => v.toLocaleString('es-ES'),
    },
    {
      title: 'Avg Price',
      dataIndex: 'avg_price',
      key: 'avg_price',
      align: 'right',
      render: (v) => `€${v.toFixed(2)}`,
    },
    {
      title: '# Invoices',
      dataIndex: 'invoice_count',
      key: 'invoice_count',
      align: 'center',
      render: (v) => <Tag>{v}</Tag>,
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>
          Analytics
        </Title>
        <RangePicker
          onChange={(dates) => {
            setDateRange({
              date_from: dates?.[0]?.format('YYYY-MM-DD'),
              date_to: dates?.[1]?.format('YYYY-MM-DD'),
            });
          }}
        />
      </div>

      <Card title="Material Price Analysis" style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Select
            showSearch
            style={{ width: 400, maxWidth: '100%' }}
            placeholder="Search and select a material to analyze..."
            filterOption={false}
            onSearch={(val) => setMaterialSearch(val)}
            onChange={(val) => setSelectedMaterialId(val as number)}
            options={(materialsData?.items || []).map((m) => ({
              value: m.id,
              label: `[${m.master_code}] ${m.normalized_description}`,
            }))}
            value={selectedMaterialId}
            notFoundContent="No materials found"
            allowClear
          />

          {selectedMaterialId ? (
            <Row gutter={[16, 16]}>
              <Col xs={24} lg={14}>
                <Card title="Price History" size="small">
                  {loadingHistory ? (
                    <Spin />
                  ) : (
                    <ReactECharts option={priceHistoryOption} style={{ height: 280 }} />
                  )}
                </Card>
              </Col>
              <Col xs={24} lg={10}>
                <Card title="Provider Comparison" size="small">
                  {loadingComparison ? (
                    <Spin />
                  ) : (
                    <ReactECharts option={providerComparisonOption} style={{ height: 280 }} />
                  )}
                </Card>
              </Col>
            </Row>
          ) : (
            <Typography.Text type="secondary">
              Select a material above to view price history and provider comparison charts.
            </Typography.Text>
          )}
        </Space>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={14}>
          <Card title="Top Materials by Spend">
            {loadingStats ? (
              <Spin />
            ) : (
              <ReactECharts option={topMaterialsOption} style={{ height: 320 }} />
            )}
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title="Spending by Family">
            <ReactECharts option={familyPieOption} style={{ height: 320 }} />
          </Card>
        </Col>
      </Row>

      <Card title="Materials Statistics" style={{ marginTop: 16 }}>
        <Table
          columns={statsColumns}
          dataSource={materialsStats || []}
          rowKey="material_id"
          loading={loadingStats}
          size="small"
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  );
}
