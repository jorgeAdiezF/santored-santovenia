import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Row,
  Col,
  Tag,
  Button,
  Typography,
  Spin,
  Alert,
  Table,
  Space,
  message,
  Descriptions,
  Badge,
} from 'antd';
import {
  ArrowLeftOutlined,
  ScanOutlined,
  CheckOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import { useDocument, useConfirmSegment, useTriggerOcr } from '../../hooks/useDocuments';
import type { DetectedDoc, SegmentStatus } from '../../types';

const { Title, Text } = Typography;

const segmentStatusColors: Record<SegmentStatus, string> = {
  detected: 'default',
  confirmed: 'blue',
  ocr_done: 'cyan',
  extracted: 'green',
  error: 'error',
};

export default function DocumentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const docId = parseInt(id || '0', 10);

  const { data: document, isLoading, error, refetch } = useDocument(docId);
  const confirmSegmentMutation = useConfirmSegment();
  const triggerOcrMutation = useTriggerOcr();

  const handleConfirmSegment = async (segmentId: number) => {
    try {
      await confirmSegmentMutation.mutateAsync({ documentId: docId, segmentId });
      message.success('Segment confirmed');
    } catch {
      message.error('Failed to confirm segment');
    }
  };

  const handleTriggerOcr = async () => {
    try {
      await triggerOcrMutation.mutateAsync(docId);
      message.success('OCR processing started');
      refetch();
    } catch {
      message.error('Failed to trigger OCR');
    }
  };

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (error || !document) {
    return (
      <Alert
        message="Document Not Found"
        description="The requested document could not be found."
        type="error"
        showIcon
        action={
          <Button onClick={() => navigate('/documents')}>Back to Documents</Button>
        }
      />
    );
  }

  const segmentColumns: ColumnsType<DetectedDoc> = [
    {
      title: '#',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: 'Type',
      dataIndex: 'doc_type',
      key: 'doc_type',
      render: (t) => <Tag>{t.toUpperCase()}</Tag>,
    },
    {
      title: 'Pages',
      key: 'pages',
      render: (_, r) => `${r.page_start} - ${r.page_end}`,
      width: 100,
    },
    {
      title: 'Confidence',
      dataIndex: 'confidence',
      key: 'confidence',
      width: 110,
      render: (c) => {
        const pct = (c * 100).toFixed(0);
        const color = c >= 0.9 ? '#52c41a' : c >= 0.7 ? '#fa8c16' : '#f5222d';
        return <Text style={{ color }}>{pct}%</Text>;
      },
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: SegmentStatus) => (
        <Badge
          status={
            status === 'extracted' ? 'success'
            : status === 'error' ? 'error'
            : status === 'confirmed' || status === 'ocr_done' ? 'processing'
            : 'default'
          }
          text={
            <Tag color={segmentStatusColors[status]}>
              {status.replace(/_/g, ' ').toUpperCase()}
            </Tag>
          }
        />
      ),
    },
    {
      title: 'Invoice',
      dataIndex: 'invoice_id',
      key: 'invoice_id',
      render: (invoiceId) =>
        invoiceId ? (
          <Button type="link" onClick={() => navigate(`/review/${invoiceId}`)}>
            #{invoiceId}
          </Button>
        ) : (
          <Text type="secondary">—</Text>
        ),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) =>
        record.status === 'detected' ? (
          <Button
            size="small"
            icon={<CheckOutlined />}
            onClick={() => handleConfirmSegment(record.id)}
            loading={confirmSegmentMutation.isPending}
          >
            Confirm
          </Button>
        ) : null,
    },
  ];

  const confirmedSegments = document.detected_docs?.filter(
    (d) => d.status === 'confirmed' || d.status === 'ocr_done'
  ) || [];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/documents')}>
          Back
        </Button>
        <Title level={3} style={{ margin: 0 }}>
          {document.original_filename}
        </Title>
      </Space>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={8}>
          <Card title="Document Info">
            <Descriptions column={1} size="small">
              <Descriptions.Item label="Status">
                <Tag color={
                  document.status === 'completed' ? 'success'
                  : document.status === 'error' ? 'error'
                  : 'processing'
                }>
                  {document.status.replace(/_/g, ' ').toUpperCase()}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Pages">{document.page_count}</Descriptions.Item>
              <Descriptions.Item label="Upload Date">
                {dayjs(document.upload_date).format('DD/MM/YYYY HH:mm')}
              </Descriptions.Item>
              {document.processed_at && (
                <Descriptions.Item label="Processed">
                  {dayjs(document.processed_at).format('DD/MM/YYYY HH:mm')}
                </Descriptions.Item>
              )}
              <Descriptions.Item label="File Size">
                {(document.file_size / 1024 / 1024).toFixed(2)} MB
              </Descriptions.Item>
            </Descriptions>

            {document.error_message && (
              <Alert
                message="Processing Error"
                description={document.error_message}
                type="error"
                showIcon
                style={{ marginTop: 12 }}
              />
            )}

            {confirmedSegments.length > 0 && (
              <Button
                type="primary"
                icon={<ScanOutlined />}
                onClick={handleTriggerOcr}
                loading={triggerOcrMutation.isPending}
                style={{ marginTop: 16, width: '100%' }}
              >
                Run OCR on Confirmed Segments
              </Button>
            )}
          </Card>
        </Col>

        <Col xs={24} lg={16}>
          <Card title={`Pages (${document.pages?.length || 0})`} style={{ marginBottom: 16 }}>
            {document.pages && document.pages.length > 0 ? (
              <Row gutter={[8, 8]}>
                {document.pages.map((page) => (
                  <Col key={page.id} xs={6} sm={4} md={3}>
                    <Card
                      size="small"
                      style={{
                        textAlign: 'center',
                        border: '1px solid #d9d9d9',
                        borderRadius: 4,
                      }}
                      styles={{ body: { padding: '8px 4px' } }}
                    >
                      <div
                        style={{
                          width: '100%',
                          aspectRatio: '0.7',
                          background: '#f5f5f5',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          marginBottom: 4,
                          borderRadius: 2,
                        }}
                      >
                        {page.thumbnail_path ? (
                          <img
                            src={`/api${page.thumbnail_path}`}
                            alt={`Page ${page.page_number}`}
                            style={{ maxWidth: '100%', maxHeight: '100%' }}
                          />
                        ) : (
                          <Text type="secondary" style={{ fontSize: 10 }}>
                            No preview
                          </Text>
                        )}
                      </div>
                      <Text type="secondary" style={{ fontSize: 11 }}>
                        p.{page.page_number}
                      </Text>
                    </Card>
                  </Col>
                ))}
              </Row>
            ) : (
              <Text type="secondary">No pages available</Text>
            )}
          </Card>

          <Card title={`Detected Invoice Segments (${document.detected_docs?.length || 0})`}>
            <Table
              columns={segmentColumns}
              dataSource={document.detected_docs || []}
              rowKey="id"
              size="small"
              pagination={false}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
