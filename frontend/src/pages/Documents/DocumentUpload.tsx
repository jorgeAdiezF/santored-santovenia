import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Upload,
  Button,
  Progress,
  Typography,
  List,
  Tag,
  Alert,
  Space,
  Divider,
} from 'antd';
import {
  InboxOutlined,
  CheckCircleOutlined,
  FileOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import type { UploadFile, UploadProps } from 'antd';
import { uploadDocuments } from '../../api/documents';
import type { Document } from '../../types';

const { Dragger } = Upload;
const { Title, Text } = Typography;

export default function DocumentUpload() {
  const navigate = useNavigate();
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploadedDocs, setUploadedDocs] = useState<Document[]>([]);
  const [error, setError] = useState<string | null>(null);

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: true,
    accept: '.pdf,.tiff,.tif,.jpg,.jpeg,.png',
    beforeUpload: (_file, newFileList) => {
      setFileList((prev) => [...prev, ...newFileList.map((f) => ({ ...f, status: 'uploading' as const }))]);
      return false;
    },
    fileList,
    onRemove: (file) => {
      setFileList((prev) => prev.filter((f) => f.uid !== file.uid));
    },
    showUploadList: true,
  };

  const handleUpload = async () => {
    if (fileList.length === 0) return;

    const files = fileList
      .map((f) => f.originFileObj as File)
      .filter((f): f is File => f != null);

    setUploading(true);
    setError(null);
    setProgress(0);

    try {
      const result = await uploadDocuments(files, (p) => setProgress(p));
      setUploadedDocs(result);
      setFileList([]);
      setProgress(100);
    } catch (err) {
      setError('Upload failed. Please check your files and try again.');
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  const statusColors: Record<string, string> = {
    uploaded: 'default',
    processing: 'processing',
    segmented: 'blue',
    ocr_done: 'cyan',
    completed: 'success',
    error: 'error',
  };

  return (
    <div>
      <Title level={3} style={{ marginBottom: 24 }}>
        Upload Documents
      </Title>

      {error && (
        <Alert
          message="Upload Error"
          description={error}
          type="error"
          showIcon
          closable
          onClose={() => setError(null)}
          style={{ marginBottom: 16 }}
        />
      )}

      <Card style={{ marginBottom: 24 }}>
        <Dragger {...uploadProps} disabled={uploading}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined style={{ fontSize: 48, color: '#1677ff' }} />
          </p>
          <p className="ant-upload-text">Click or drag files to this area to upload</p>
          <p className="ant-upload-hint">
            Support for PDF, TIFF, JPG, PNG files. Multiple files can be uploaded at once.
          </p>
        </Dragger>

        {fileList.length > 0 && (
          <>
            <Divider />
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text>
                {fileList.length} file{fileList.length !== 1 ? 's' : ''} selected
              </Text>
              <Space>
                <Button onClick={() => setFileList([])} disabled={uploading}>
                  Clear All
                </Button>
                <Button
                  type="primary"
                  onClick={handleUpload}
                  loading={uploading}
                  disabled={fileList.length === 0}
                >
                  {uploading ? 'Uploading...' : 'Start Upload'}
                </Button>
              </Space>
            </div>
          </>
        )}

        {uploading && (
          <div style={{ marginTop: 16 }}>
            <Progress percent={progress} status="active" />
            <Text type="secondary">Uploading and processing files...</Text>
          </div>
        )}
      </Card>

      {uploadedDocs.length > 0 && (
        <Card
          title={
            <Space>
              <CheckCircleOutlined style={{ color: '#52c41a' }} />
              <span>Upload Complete - {uploadedDocs.length} document(s) processed</span>
            </Space>
          }
        >
          <List
            dataSource={uploadedDocs}
            renderItem={(doc) => (
              <List.Item
                key={doc.id}
                actions={[
                  <Button
                    key="view"
                    type="link"
                    icon={<EyeOutlined />}
                    onClick={() => navigate(`/documents/${doc.id}`)}
                  >
                    View Details
                  </Button>,
                ]}
              >
                <List.Item.Meta
                  avatar={<FileOutlined style={{ fontSize: 24, color: '#1677ff' }} />}
                  title={
                    <Space>
                      <Text strong>{doc.original_filename}</Text>
                      <Tag color={statusColors[doc.status] || 'default'}>
                        {doc.status.replace(/_/g, ' ').toUpperCase()}
                      </Tag>
                    </Space>
                  }
                  description={
                    <Space>
                      <Text type="secondary">{doc.page_count} pages</Text>
                      {doc.detected_docs && (
                        <Text type="secondary">
                          {doc.detected_docs.length} invoice segment(s) detected
                        </Text>
                      )}
                    </Space>
                  }
                />
              </List.Item>
            )}
          />

          <Divider />
          <Space>
            <Button onClick={() => navigate('/documents')}>View All Documents</Button>
            <Button
              type="primary"
              onClick={() => {
                setUploadedDocs([]);
                setFileList([]);
                setProgress(0);
              }}
            >
              Upload More
            </Button>
          </Space>
        </Card>
      )}
    </div>
  );
}
