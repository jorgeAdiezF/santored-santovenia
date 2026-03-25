import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Table,
  Button,
  Tag,
  Space,
  Input,
  Select,
  DatePicker,
  Card,
  Typography,
  Popconfirm,
  message,
  Row,
  Col,
} from 'antd';
import {
  UploadOutlined,
  EyeOutlined,
  DeleteOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import { useDocuments, useDeleteDocument } from '../../hooks/useDocuments';
import type { DocumentListItem, DocumentStatus, ListParams } from '../../types';

const { Title } = Typography;
const { RangePicker } = DatePicker;

const statusColors: Record<DocumentStatus, string> = {
  uploaded: 'default',
  processing: 'processing',
  segmented: 'blue',
  ocr_done: 'cyan',
  completed: 'success',
  error: 'error',
};

const statusOptions = [
  { value: '', label: 'All Statuses' },
  { value: 'uploaded', label: 'Uploaded' },
  { value: 'processing', label: 'Processing' },
  { value: 'segmented', label: 'Segmented' },
  { value: 'ocr_done', label: 'OCR Done' },
  { value: 'completed', label: 'Completed' },
  { value: 'error', label: 'Error' },
];

export default function DocumentList() {
  const navigate = useNavigate();
  const [params, setParams] = useState<ListParams>({ page: 1, size: 20 });
  const [searchText, setSearchText] = useState('');

  const { data, isLoading } = useDocuments(params);
  const deleteMutation = useDeleteDocument();

  const handleDelete = async (id: number) => {
    try {
      await deleteMutation.mutateAsync(id);
      message.success('Document deleted successfully');
    } catch {
      message.error('Failed to delete document');
    }
  };

  const handleSearch = () => {
    setParams((prev) => ({ ...prev, search: searchText, page: 1 }));
  };

  const columns: ColumnsType<DocumentListItem> = [
    {
      title: 'Filename',
      dataIndex: 'original_filename',
      key: 'filename',
      ellipsis: true,
      render: (text, record) => (
        <a onClick={() => navigate(`/documents/${record.id}`)}>{text}</a>
      ),
    },
    {
      title: 'Upload Date',
      dataIndex: 'upload_date',
      key: 'upload_date',
      render: (d) => dayjs(d).format('DD/MM/YYYY HH:mm'),
      width: 160,
      sorter: true,
    },
    {
      title: 'Size',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      render: (size) => {
        if (size < 1024) return `${size} B`;
        if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
        return `${(size / 1024 / 1024).toFixed(1)} MB`;
      },
    },
    {
      title: 'Pages',
      dataIndex: 'page_count',
      key: 'page_count',
      width: 80,
      align: 'center',
    },
    {
      title: 'Detected',
      dataIndex: 'detected_count',
      key: 'detected_count',
      width: 90,
      align: 'center',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 130,
      render: (status: DocumentStatus) => (
        <Tag color={statusColors[status] || 'default'}>
          {status.replace(/_/g, ' ').toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/documents/${record.id}`)}
            title="View"
          />
          <Popconfirm
            title="Delete Document"
            description="Are you sure you want to delete this document?"
            onConfirm={() => handleDelete(record.id)}
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

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>
          Documents
        </Title>
        <Button
          type="primary"
          icon={<UploadOutlined />}
          onClick={() => navigate('/documents/upload')}
        >
          Upload Documents
        </Button>
      </div>

      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[12, 12]} align="middle">
          <Col xs={24} sm={10} md={8}>
            <Input
              placeholder="Search by filename..."
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
                if (dates && dates[0] && dates[1]) {
                  setParams((prev) => ({
                    ...prev,
                    date_from: dates[0]!.format('YYYY-MM-DD'),
                    date_to: dates[1]!.format('YYYY-MM-DD'),
                    page: 1,
                  }));
                } else {
                  setParams((prev) => ({
                    ...prev,
                    date_from: undefined,
                    date_to: undefined,
                    page: 1,
                  }));
                }
              }}
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
            showTotal: (total) => `Total ${total} documents`,
            onChange: (page, pageSize) =>
              setParams((prev) => ({ ...prev, page, size: pageSize })),
          }}
        />
      </Card>
    </div>
  );
}
