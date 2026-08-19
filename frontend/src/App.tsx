import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

// Helper: chuyển đổi thời gian UTC từ backend sang giờ địa phương
const formatUTCDate = (utcStr: string) => {
  if (!utcStr) return '';
  // Đảm bảo chuỗi datetime từ backend được hiểu đúng là UTC
  const dateStr = utcStr.endsWith('Z') ? utcStr : utcStr + 'Z';
  return new Date(dateStr).toLocaleString('vi-VN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    hour12: false
  });
};

// ── SVG Icon Components (Professional Vector Icons) ─────────────────────────
const I = {
  cloud: <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/></svg>,
  folder: <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2z"/></svg>,
  folderPlus: <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2z"/><line x1="12" y1="10" x2="12" y2="16"/><line x1="9" y1="13" x2="15" y2="13"/></svg>,
  file: <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>,
  filePdf: <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#e74c3c" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="9" y1="15" x2="15" y2="15"/></svg>,
  fileImage: <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#8e44ad" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>,
  upload: <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/><path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/></svg>,
  download: <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="8 17 12 21 16 17"/><line x1="12" y1="12" x2="12" y2="21"/><path d="M20.88 18.09A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.29"/></svg>,
  search: <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>,
  users: <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>,
  usersPlus: <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/></svg>,
  user: <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>,
  trash: <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>,
  edit: <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>,
  share: <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>,
  clock: <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>,
  link: <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>,
  copy: <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>,
  mail: <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>,
  undo: <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>,
  eye: <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>,
  comment: <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>,
  inbox: <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg>,
  lock: <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>,
  globe: <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>,
  dropzone: <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/><path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/></svg>,
  x: <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>,
  menu: <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>,
};

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

interface Folder {
  id: string;
  name: string;
  parent_id: string | null;
  description: string;
  created_by: string;
  is_deleted: boolean;
  tags: string[];
  created_at: string;
}

interface Document {
  id: string;
  name: string;
  folder_id: string | null;
  storage_path: string;
  file_size: number;
  mime_type: string;
  current_version: number;
  description: string;
  is_deleted: boolean;
  tags: string[];
  created_by: string;
  created_at: string;
}

interface Collaborator {
  id: string;
  resource_id: string;
  resource_type: string;
  user_id: string;
  user_email: string;
  group_name: string | null;
  share_type: string;
  access_level: 'viewer' | 'editor';
}

interface GroupMember {
  id: string;
  email: string;
  full_name: string;
}

interface StudyGroup {
  id: string;
  name: string;
  description: string;
  created_by: string;
  members: GroupMember[];
  invite_code: string;
  pending_members: {
    user_id: string;
    email: string;
    full_name: string;
  }[];
  created_at: string;
  updated_at: string;
}

interface Notification {
  id: string;
  user_id: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

interface Version {
  id: string;
  document_id: string;
  version_number: number;
  storage_path: string;
  file_size: number;
  created_by: string;
  change_log: string;
  created_at: string;
}

interface Comment {
  id: string;
  document_id: string;
  user_id: string;
  user_name: string;
  content: string;
  created_at: string;
}

interface Activity {
  id: string;
  user_id: string | null;
  user_name: string;
  action: string;
  resource_name: string;
  details: string;
  created_at: string;
}

function App() {
  // Auth state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [isLoginTab, setIsLoginTab] = useState(true);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [user, setUser] = useState<User | null>(null);

  // App UI state
  const [currentFolderId, setCurrentFolderId] = useState<string | null>(null);
  const [folders, setFolders] = useState<Folder[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [folderPath, setFolderPath] = useState<{ id: string | null; name: string; isGroupRoot?: boolean; group?: StudyGroup }[]>([{ id: null, name: 'Trang chủ' }]);

  // Search, sort, filter
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'newest' | 'oldest' | 'alphabetical'>('newest');
  const [selectedTag, setSelectedTag] = useState<string | null>(null);

  // Sidebar tab selection: 'files' | 'activities' | 'trash' | 'groups'
  const [sidebarTab, setSidebarTab] = useState<'files' | 'activities' | 'trash' | 'groups'>('files');
  const [activitiesList, setActivitiesList] = useState<Activity[]>([]);

  // Study Groups
  const [groups, setGroups] = useState<StudyGroup[]>([]);
  const [showCreateGroup, setShowCreateGroup] = useState(false);
  const [newGroupName, setNewGroupName] = useState('');
  const [newGroupDesc, setNewGroupDesc] = useState('');
  const [showGroupDetail, setShowGroupDetail] = useState<StudyGroup | null>(null);
  const [inviteMemberEmail, setInviteMemberEmail] = useState('');
  const [joinInviteCode, setJoinInviteCode] = useState('');
  const [editGroupTarget, setEditGroupTarget] = useState<{ id: string; name: string; description: string } | null>(null);

  // Notifications
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showNotifDropdown, setShowNotifDropdown] = useState(false);

  // Edit Folder/Document Modal
  const [editTarget, setEditTarget] = useState<{ id: string; type: 'folder' | 'document'; name: string; description: string; tags: string } | null>(null);

  // Share modal: share type toggle
  const [shareType, setShareType] = useState<'user' | 'group'>('user');
  const [shareGroupId, setShareGroupId] = useState('');

  // Storage Quota
  const [quotaUsed, setQuotaUsed] = useState(0);
  const [quotaLimit, setQuotaLimit] = useState(52428800); // Default 50MB

  // Modals & Drawers state
  const [showCreateFolder, setShowCreateFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [newFolderDesc, setNewFolderDesc] = useState('');
  const [newFolderTags, setNewFolderTags] = useState('');

  // Upload modal state
  const [uploadFileObj, setUploadFileObj] = useState<File | null>(null);
  const [uploadFileName, setUploadFileName] = useState('');
  const [uploadDescription, setUploadDescription] = useState('');
  const [uploadTags, setUploadTags] = useState('');

  const [showShareModal, setShowShareModal] = useState<{ id: string; type: 'folder' | 'document'; name: string } | null>(null);
  const [collaborators, setCollaborators] = useState<Collaborator[]>([]);
  const [shareEmail, setShareEmail] = useState('');
  const [shareLevel, setShareLevel] = useState<'viewer' | 'editor'>('viewer');
  const [shareLinkAccess, setShareLinkAccess] = useState<'restricted' | 'anyone'>('restricted');
  const [shareLinkLevel, setShareLinkLevel] = useState<'viewer' | 'editor'>('viewer');

  const [showHistoryDrawer, setShowHistoryDrawer] = useState<{ id: string; name: string } | null>(null);
  const [versions, setVersions] = useState<Version[]>([]);
  const [versionChangeLog, setVersionChangeLog] = useState('');

  // Preview & Comments
  const [previewDoc, setPreviewDoc] = useState<{ doc: Document; presignedUrl: string } | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState('');
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [foldersExpanded, setFoldersExpanded] = useState(true);
  const [docsExpanded, setDocsExpanded] = useState(true);

  const [groupFolders, setGroupFolders] = useState<Folder[]>([]);
  const [groupDocs, setGroupDocs] = useState<Document[]>([]);
  const [loadingGroupResources, setLoadingGroupResources] = useState(false);
  const [groupSidebarOpen, setGroupSidebarOpen] = useState(true);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const groupFileInputRef = useRef<HTMLInputElement>(null);
  const newVersionInputRef = useRef<HTMLInputElement>(null);

  const [trashFolders, setTrashFolders] = useState<Folder[]>([]);
  const [trashDocuments, setTrashDocuments] = useState<Document[]>([]);

  // Drag and drop / Progress state
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<{ [key: string]: number }>({});

  // Notification alert state
  const [message, setMessage] = useState<{ text: string; isError: boolean } | null>(null);
  const [loading, setLoading] = useState(false);

  // Auto fetch user info, quota, notifications and root workspace content
  useEffect(() => {
    const handleUrlQueryParams = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const previewDocId = urlParams.get('previewDoc');
      if (previewDocId && token) {
        try {
          const headers = { Authorization: `Bearer ${token}` };
          const res = await axios.get(`${API_BASE_URL}/documents/${previewDocId}`, { headers });
          handlePreviewDocument(res.data);
          window.history.replaceState({}, document.title, window.location.pathname);
        } catch (err: any) {
          showNotification('Không thể mở tài liệu chia sẻ hoặc liên kết đã hết hạn.', true);
        }
      }
    };

    if (token) {
      fetchUserInfo();
      fetchQuota();
      fetchNotifications();
      fetchGroups();
      handleUrlQueryParams();
    }
  }, [token]);

  // Close context dropdown on outside click
  useEffect(() => {
    const handleCloseMenu = () => setActiveMenuId(null);
    window.addEventListener('click', handleCloseMenu);
    return () => window.removeEventListener('click', handleCloseMenu);
  }, []);

  // Poll notifications every 30s
  useEffect(() => {
    if (!token) return;
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, [token]);

  useEffect(() => {
    if (token) {
      if (sidebarTab === 'files') {
        fetchWorkspaceContent();
      } else if (sidebarTab === 'trash') {
        fetchTrashContent();
      } else if (sidebarTab === 'activities') {
        fetchActivitiesContent();
      } else if (sidebarTab === 'groups') {
        fetchGroups();
      }
    }
    // Reset selected tag when tab changes
    setSelectedTag(null);
  }, [token, currentFolderId, sidebarTab]);

  const fetchUserInfo = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setUser(res.data);
    } catch (err) {
      handleLogout();
    }
  };

  const fetchQuota = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/documents/quota`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setQuotaUsed(res.data.used_bytes);
      setQuotaLimit(res.data.limit_bytes);
    } catch (err) {
      console.error('Lỗi tải dung lượng quota:', err);
    }
  };

  const fetchWorkspaceContent = async () => {
    setLoading(true);
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };

      // Fetch subfolders
      const folderUrl = currentFolderId ? `${API_BASE_URL}/folders?parent_id=${currentFolderId}` : `${API_BASE_URL}/folders`;
      const folderRes = await axios.get(folderUrl, { headers });
      setFolders(folderRes.data);

      // Fetch documents in folder (using search with q="" as listing)
      const docUrl = currentFolderId ? `${API_BASE_URL}/documents/search?folder_id=${currentFolderId}` : `${API_BASE_URL}/documents/search`;
      const docRes = await axios.get(docUrl, { headers });
      setDocuments(docRes.data);
    } catch (err: any) {
      showNotification(getErrorMessage(err, 'Lỗi tải nội dung thư mục.'), true);
    } finally {
      setLoading(false);
    }
  };

  const fetchTrashContent = async () => {
    setLoading(true);
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      const foldersRes = await axios.get(`${API_BASE_URL}/folders/trash`, { headers });
      const docsRes = await axios.get(`${API_BASE_URL}/documents/trash`, { headers });
      setTrashFolders(foldersRes.data);
      setTrashDocuments(docsRes.data);
    } catch (err: any) {
      showNotification(getErrorMessage(err, 'Lỗi tải nội dung thùng rác.'), true);
    } finally {
      setLoading(false);
    }
  };

  const fetchActivitiesContent = async () => {
    setLoading(true);
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      const res = await axios.get(`${API_BASE_URL}/activities`, { headers });
      setActivitiesList(res.data);
    } catch (err: any) {
      showNotification(getErrorMessage(err, 'Lỗi tải lịch sử hoạt động.'), true);
    } finally {
      setLoading(false);
    }
  };

  const getErrorMessage = (error: any, defaultMsg: string): string => {
    if (error.response?.data?.detail) {
      const detail = error.response.data.detail;
      if (typeof detail === 'string') return detail;
      if (Array.isArray(detail)) {
        return detail.map((d: any) => `${d.loc?.join('/') || ''}: ${d.msg || d.detail}`).join(', ');
      }
    }
    return defaultMsg;
  };

  const showNotification = (text: string, isError: boolean = false) => {
    setMessage({ text, isError });
    setTimeout(() => setMessage(null), 5000);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setFolders([]);
    setDocuments([]);
    setFolderPath([{ id: null, name: 'Trang chủ' }]);
    setCurrentFolderId(null);
    setSidebarTab('files');
    setSelectedTag(null);
    showNotification('Đã đăng xuất khỏi hệ thống.');
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE_URL}/auth/login`, { email, password });
      localStorage.setItem('token', res.data.access_token);
      setToken(res.data.access_token);
      setUser(res.data.user);
      showNotification('Đăng nhập thành công!');
    } catch (err: any) {
      showNotification(getErrorMessage(err, 'Đăng nhập thất bại. Kiểm tra lại thông tin.'), true);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API_BASE_URL}/auth/register`, { email, password, full_name: fullName });
      showNotification('Đăng ký tài khoản thành công! Hãy đăng nhập.');
      setIsLoginTab(true);
    } catch (err: any) {
      showNotification(getErrorMessage(err, 'Đăng ký thất bại. Email có thể đã tồn tại.'), true);
    } finally {
      setLoading(false);
    }
  };

  // Navigations inside explorer
  const navigateToFolder = (folder: Folder) => {
    setCurrentFolderId(folder.id);
    setFolderPath([...folderPath, { id: folder.id, name: folder.name }]);
  };

  const navigateToBreadcrumb = (index: number) => {
    const target = folderPath[index];
    if (!target) return;

    if (target.isGroupRoot && target.group) {
      setSidebarTab('groups');
      setShowGroupDetail(target.group);
      setFolderPath([{ id: null, name: 'Trang chủ' }]);
      setCurrentFolderId(null);
      return;
    }
    if (index === 0 && target.name === 'Nhóm học tập của tôi') {
      setSidebarTab('groups');
      setShowGroupDetail(null);
      setFolderPath([{ id: null, name: 'Trang chủ' }]);
      setCurrentFolderId(null);
      return;
    }

    setCurrentFolderId(target.id);
    setFolderPath(folderPath.slice(0, index + 1));
  };

  // Folder Operations
  const handleCreateFolder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFolderName.trim()) return;

    // Parse comma separated tags
    const tagsList = newFolderTags.split(',')
      .map(t => t.trim())
      .filter(t => t !== '');

    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      const res = await axios.post(`${API_BASE_URL}/folders`, {
        name: newFolderName,
        parent_id: showGroupDetail ? null : currentFolderId,
        description: newFolderDesc,
        tags: tagsList
      }, { headers });

      const newFolder = res.data;

      // Nếu đang ở trong nhóm học tập, tự động chia sẻ cho nhóm
      if (showGroupDetail) {
        await axios.post(`${API_BASE_URL}/permissions`, {
          resource_id: newFolder.id,
          resource_type: 'folder',
          share_type: 'group',
          group_id: showGroupDetail.id,
          access_level: 'editor'
        }, { headers });
        fetchGroupResources(showGroupDetail.id);
      }

      showNotification('Tạo thư mục thành công!');
      setShowCreateFolder(false);
      setNewFolderName('');
      setNewFolderDesc('');
      setNewFolderTags('');
      fetchWorkspaceContent();
    } catch (err: any) {
      showNotification(getErrorMessage(err, 'Không thể tạo thư mục.'), true);
    }
  };

  // Prepare file upload (Open details modal)
  const handleSelectFile = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setUploadFileObj(files[0]);
    setUploadFileName(files[0].name);
    setUploadDescription('');
    setUploadTags('');
  };

  // Execute file upload multipart request
  const executeUploadFile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFileObj) return;

    const file = uploadFileObj;
    const formData = new FormData();
    formData.append('file', file);
    if (showGroupDetail) {
      // Đang ở trong nhóm học tập, lưu ở gốc của nhóm
    } else if (currentFolderId) {
      formData.append('folder_id', currentFolderId);
    }
    formData.append('description', uploadDescription || 'Tải lên từ giao diện web');
    formData.append('tags', uploadTags);
    if (uploadFileName.trim()) {
      formData.append('custom_name', uploadFileName.trim());
    }

    const finalDisplayName = uploadFileName.trim() || file.name;
    setUploadFileObj(null); // Close modal first

    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };

      // Axios upload progress monitoring
      const res = await axios.post(`${API_BASE_URL}/documents/upload`, formData, {
        headers,
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(prev => ({ ...prev, [file.name]: percent }));
          }
        }
      });

      const newDoc = res.data;

      // Nếu đang ở trong nhóm học tập, tự động chia sẻ cho nhóm
      if (showGroupDetail) {
        await axios.post(`${API_BASE_URL}/permissions`, {
          resource_id: newDoc.id,
          resource_type: 'document',
          share_type: 'group',
          group_id: showGroupDetail.id,
          access_level: 'editor'
        }, { headers });
        fetchGroupResources(showGroupDetail.id);
        fetchGroups(); // Refresh quota
      }

      showNotification(`Đã tải lên tệp '${finalDisplayName}' thành công!`);
      setTimeout(() => {
        setUploadProgress(prev => {
          const next = { ...prev };
          delete next[file.name];
          return next;
        });
      }, 2000);

      fetchWorkspaceContent();
      fetchQuota();
    } catch (err: any) {
      showNotification(getErrorMessage(err, 'Lỗi tải lên tài liệu.'), true);
      setUploadProgress(prev => {
        const next = { ...prev };
        delete next[file.name];
        return next;
      });
    }
  };

  // Drag and Drop handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleSelectFile(e.dataTransfer.files);
    }
  };

  // File Download / Secure presigned url
  const handleDownloadFile = async (doc: Document) => {
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      const res = await axios.get(`${API_BASE_URL}/documents/${doc.id}/presigned-url`, { headers });
      window.open(res.data.url, '_blank');
    } catch (err: any) {
      showNotification(getErrorMessage(err, 'Lỗi lấy liên kết tải file.'), true);
    }
  };

  // Web File Preview & Comments
  const handlePreviewDocument = async (doc: Document) => {
    setLoading(true);
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      const urlRes = await axios.get(`${API_BASE_URL}/documents/${doc.id}/presigned-url`, { headers });
      setPreviewDoc({ doc, presignedUrl: urlRes.data.url });

      // Load comments
      const commentRes = await axios.get(`${API_BASE_URL}/documents/${doc.id}/comments`, { headers });
      setComments(commentRes.data);
    } catch (err: any) {
      showNotification(getErrorMessage(err, 'Lỗi tải thông tin xem trước tài liệu.'), true);
    } finally {
      setLoading(false);
    }
  };

  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim() || !previewDoc) return;
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      const res = await axios.post(`${API_BASE_URL}/documents/${previewDoc.doc.id}/comments`, {
        content: newComment
      }, { headers });
      setComments([...comments, res.data]);
      setNewComment('');
    } catch (err: any) {
      showNotification(getErrorMessage(err, 'Không thể gửi bình luận.'), true);
    }
  };

  // Sharing ACL Permissions
  const openShareModal = async (resourceId: string, type: 'folder' | 'document', name: string) => {
    setShowShareModal({ id: resourceId, type, name });
    setShareEmail('');
    setCollaborators([]);
    setShareLinkAccess('restricted');
    setShareLinkLevel('viewer');

    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      const res = await axios.get(`${API_BASE_URL}/permissions/${type}/${resourceId}`, { headers });
      setCollaborators(res.data);

      // Load link sharing configuration
      const linkRes = await axios.get(`${API_BASE_URL}/permissions/link-sharing/${type}/${resourceId}`, { headers });
      setShareLinkAccess(linkRes.data.share_link_access);
      setShareLinkLevel(linkRes.data.share_link_level);
    } catch (err: any) {
      console.error('Không thể tải cấu hình chia sẻ qua liên kết:', err);
    }
  };

  const handleUpdateLinkSharing = async (access: 'restricted' | 'anyone', level: 'viewer' | 'editor') => {
    if (!showShareModal) return;
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      const res = await axios.post(
        `${API_BASE_URL}/permissions/link-sharing/${showShareModal.type}/${showShareModal.id}`,
        {
          share_link_access: access,
          share_link_level: level
        },
        { headers }
      );
      setShareLinkAccess(res.data.share_link_access);
      setShareLinkLevel(res.data.share_link_level);
      showNotification('Đã cập nhật cấu hình chia sẻ qua liên kết!');
    } catch (err: any) {
      showNotification(getErrorMessage(err, 'Không thể cập nhật cấu hình chia sẻ qua liên kết.'), true);
    }
  };

  const handleRevokeShare = async (permId: string) => {
    if (!showShareModal) return;
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      await axios.delete(`${API_BASE_URL}/permissions/${permId}`, { headers });
      showNotification('Đã thu hồi quyền chia sẻ.');
      const res = await axios.get(`${API_BASE_URL}/permissions/${showShareModal.type}/${showShareModal.id}`, { headers });
      setCollaborators(res.data);
    } catch (err: any) {
      showNotification(getErrorMessage(err, 'Không thể thu hồi quyền chia sẻ.'), true);
    }
  };

  // Version Control History Drawer
  const openHistoryDrawer = async (doc: Document) => {
    setShowHistoryDrawer({ id: doc.id, name: doc.name });
    setVersions([]);
    setVersionChangeLog('');
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      const res = await axios.get(`${API_BASE_URL}/versions/${doc.id}`, { headers });
      setVersions(res.data);
    } catch (err: any) {
      showNotification(getErrorMessage(err, 'Không thể tải lịch sử phiên bản.'), true);
    }
  };

  const handleUploadNewVersion = async (files: FileList | null) => {
    if (!files || files.length === 0 || !showHistoryDrawer) return;
    const file = files[0];
    const formData = new FormData();
    formData.append('file', file);
    formData.append('change_log', versionChangeLog || 'Cập nhật phiên bản mới');

    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      await axios.post(`${API_BASE_URL}/documents/${showHistoryDrawer.id}/versions`, formData, { headers });
      showNotification(`Đã cập nhật phiên bản mới cho '${file.name}' thành công!`);
      setVersionChangeLog('');

      const res = await axios.get(`${API_BASE_URL}/versions/${showHistoryDrawer.id}`, { headers });
      setVersions(res.data);
      fetchWorkspaceContent();
      fetchQuota();
    } catch (err: any) {
      showNotification(getErrorMessage(err, 'Lỗi tải lên phiên bản mới.'), true);
    }
  };

  const handleRollback = async (versionNumber: number) => {
    if (!showHistoryDrawer) return;
    if (!window.confirm(`Bạn có chắc muốn khôi phục về Phiên bản thứ ${versionNumber}?`)) return;
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      await axios.post(`${API_BASE_URL}/versions/${showHistoryDrawer.id}/rollback/${versionNumber}`, {}, { headers });
      showNotification('Đã rollback khôi phục phiên bản thành công!');
      const res = await axios.get(`${API_BASE_URL}/versions/${showHistoryDrawer.id}`, { headers });
      setVersions(res.data);
      fetchWorkspaceContent();
      fetchQuota();
    } catch (err: any) {
      showNotification(getErrorMessage(err, 'Lỗi khi rollback phiên bản.'), true);
    }
  };

  // Trash Operations (Soft Delete, Restore, Hard Delete)
  const handleSoftDelete = async (id: string, type: 'folder' | 'document') => {
    if (!window.confirm('Bạn có chắc muốn đưa tài nguyên này vào thùng rác?')) return;
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      const endpoint = type === 'folder' ? `${API_BASE_URL}/folders/${id}` : `${API_BASE_URL}/documents/${id}`;
      await axios.delete(endpoint, { headers });
      showNotification('Đã chuyển tài nguyên vào Thùng rác.');
      fetchWorkspaceContent();
      fetchQuota();
      if (showGroupDetail) {
        fetchGroupResources(showGroupDetail.id);
      }
    } catch (err: any) {
      showNotification(getErrorMessage(err, 'Lỗi khi xóa mềm tài nguyên.'), true);
    }
  };

  const handleRestore = async (id: string, type: 'folder' | 'document') => {
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      const endpoint = type === 'folder' ? `${API_BASE_URL}/folders/${id}/restore` : `${API_BASE_URL}/documents/${id}/restore`;
      await axios.post(endpoint, {}, { headers });
      showNotification('Khôi phục tài nguyên thành công!');
      fetchTrashContent();
      fetchQuota();
    } catch (err: any) {
      showNotification(getErrorMessage(err, 'Lỗi khôi phục tài nguyên.'), true);
    }
  };

  const handleHardDelete = async (id: string, type: 'folder' | 'document') => {
    if (!window.confirm('CẢNH BÁO: Hành động này sẽ XÓA VĨNH VIỄN tệp tin và các phiên bản khỏi Cloud Storage. Không thể khôi phục. Bạn vẫn muốn tiếp tục?')) return;
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      const endpoint = type === 'folder' ? `${API_BASE_URL}/folders/${id}/hard` : `${API_BASE_URL}/documents/${id}/hard`;
      if (type === 'document') {
        await axios.delete(endpoint, { headers });
      } else {
        showNotification('Tính năng xóa cứng thư mục hiện chưa cấu hình.', true);
        return;
      }
      showNotification('Đã xóa vĩnh viễn tài nguyên.');
      fetchTrashContent();
      fetchQuota();
    } catch (err: any) {
      showNotification(getErrorMessage(err, 'Lỗi khi xóa vĩnh viễn.'), true);
    }
  };

  const formatBytes = (bytes: number, decimals = 2) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  };

  // ── Study Groups Functions ─────────────────────────────────────────────
  const fetchGroups = async () => {
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      const res = await axios.get(`${API_BASE_URL}/groups`, { headers });
      setGroups(res.data);
    } catch (err) {
      console.error('Lỗi tải danh sách nhóm:', err);
    }
  };

  const handleCreateGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newGroupName.trim()) return;
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      await axios.post(`${API_BASE_URL}/groups`, {
        name: newGroupName,
        description: newGroupDesc
      }, { headers });
      showNotification('Tạo nhóm học tập thành công!');
      setShowCreateGroup(false);
      setNewGroupName('');
      setNewGroupDesc('');
      fetchGroups();
    } catch (err: any) {
      showNotification(getErrorMessage(err, 'Không thể tạo nhóm.'), true);
    }
  };

  const handleInviteMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!showGroupDetail || !inviteMemberEmail.trim()) return;
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      const res = await axios.post(`${API_BASE_URL}/groups/${showGroupDetail.id}/members`, {
        email: inviteMemberEmail
      }, { headers });
      showNotification(`Đã mời ${inviteMemberEmail} vào nhóm!`);
      setInviteMemberEmail('');
      setShowGroupDetail(res.data);
      fetchGroups();
    } catch (err: any) {
      showNotification(getErrorMessage(err, 'Không thể mời thành viên.'), true);
    }
  };

  const handleRemoveMember = async (memberId: string) => {
    if (!showGroupDetail) return;
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      const res = await axios.delete(`${API_BASE_URL}/groups/${showGroupDetail.id}/members/${memberId}`, { headers });
      showNotification('Đã xóa thành viên khỏi nhóm.');
      setShowGroupDetail(res.data);
      fetchGroups();
    } catch (err: any) {
      showNotification(getErrorMessage(err, 'Không thể xóa thành viên.'), true);
    }
  };

  const handleJoinViaLink = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!joinInviteCode.trim()) return;

    let code = joinInviteCode.trim();
    if (code.includes('/join/')) {
      code = code.split('/join/').pop() || '';
    }
    // Strip trailing slashes, query parameters, and hashes
    code = code.split('?')[0].split('#')[0].replace(/\/+$/, '');

    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      await axios.post(`${API_BASE_URL}/groups/join/${code}`, {}, { headers });
      showNotification('Yêu cầu tham gia nhóm đã được gửi đi. Vui lòng chờ chủ nhóm phê duyệt!');
      setJoinInviteCode('');
      fetchGroups();
    } catch (err: any) {
      showNotification(getErrorMessage(err, 'Mã mời không hợp lệ hoặc nhóm không tồn tại.'), true);
    }
  };

  const fetchGroupResources = async (groupId: string) => {
    setLoadingGroupResources(true);
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      const res = await axios.get(`${API_BASE_URL}/groups/${groupId}/resources`, { headers });
      setGroupFolders(res.data.folders);
      setGroupDocs(res.data.documents);
    } catch (err) {
      console.error("Lỗi tải tài nguyên nhóm:", err);
    } finally {
      setLoadingGroupResources(false);
    }
  };

  useEffect(() => {
    if (showGroupDetail) {
      fetchGroupResources(showGroupDetail.id);
    } else {
      setGroupFolders([]);
      setGroupDocs([]);
    }
  }, [showGroupDetail]);



  const handleCreateGroupFolder = () => {
    setShowCreateFolder(true);
  };

  const handleApproveRequest = async (groupId: string, userId: string) => {
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      const res = await axios.post(`${API_BASE_URL}/groups/${groupId}/approve/${userId}`, {}, { headers });
      showNotification('Đã phê duyệt yêu cầu tham gia nhóm.');
      setShowGroupDetail(res.data);
      fetchGroups();
    } catch (err: any) {
      showNotification(getErrorMessage(err, 'Không thể phê duyệt yêu cầu.'), true);
    }
  };

  const handleRejectRequest = async (groupId: string, userId: string) => {
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      const res = await axios.post(`${API_BASE_URL}/groups/${groupId}/reject/${userId}`, {}, { headers });
      showNotification('Đã từ chối yêu cầu tham gia nhóm.');
      setShowGroupDetail(res.data);
      fetchGroups();
    } catch (err: any) {
      showNotification(getErrorMessage(err, 'Không thể từ chối yêu cầu.'), true);
    }
  };

  const handleCopyInviteLink = (inviteCode: string) => {
    const link = `${window.location.origin}/join/${inviteCode}`;
    navigator.clipboard.writeText(link).then(() => {
      showNotification('Đã sao chép link mời vào clipboard!');
    }).catch(() => {
      window.prompt('Sao chép link mời bên dưới:', link);
    });
  };

  // ── Group Edit & Delete Handlers ─────────────────────────────────────
  const handleOpenEditGroup = (g: StudyGroup) => {
    setEditGroupTarget({ id: g.id, name: g.name, description: g.description || '' });
  };

  const handleSaveEditGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editGroupTarget) return;
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      const res = await axios.patch(`${API_BASE_URL}/groups/${editGroupTarget.id}`, {
        name: editGroupTarget.name,
        description: editGroupTarget.description
      }, { headers });
      showNotification('Đã cập nhật thông tin nhóm học tập!');
      setEditGroupTarget(null);
      fetchGroups();
      if (showGroupDetail && showGroupDetail.id === editGroupTarget.id) {
        setShowGroupDetail(res.data);
      }
    } catch (err: any) {
      showNotification(getErrorMessage(err, 'Lỗi cập nhật thông tin nhóm.'), true);
    }
  };

  const handleDeleteGroup = async (groupId: string, groupName: string) => {
    if (!window.confirm(`Bạn có chắc chắn muốn giải tán / xóa nhóm học tập "${groupName}"?`)) return;
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      await axios.delete(`${API_BASE_URL}/groups/${groupId}`, { headers });
      showNotification(`Đã xóa nhóm học tập "${groupName}".`);
      if (showGroupDetail && showGroupDetail.id === groupId) {
        setShowGroupDetail(null);
      }
      fetchGroups();
    } catch (err: any) {
      showNotification(getErrorMessage(err, 'Lỗi khi xóa nhóm học tập.'), true);
    }
  };

  // ── Notifications Functions ────────────────────────────────────────────
  const fetchNotifications = async () => {
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      const res = await axios.get(`${API_BASE_URL}/notifications`, { headers });
      setNotifications(res.data);
    } catch (err) {
      console.error('Lỗi tải thông báo:', err);
    }
  };

  const handleMarkNotifRead = async (notifId: string) => {
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      await axios.post(`${API_BASE_URL}/notifications/${notifId}/read`, {}, { headers });
      fetchNotifications();
    } catch (err) {
      console.error('Lỗi cập nhật thông báo:', err);
    }
  };

  const handleMarkAllNotifsRead = async () => {
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      await axios.post(`${API_BASE_URL}/notifications/read-all`, {}, { headers });
      fetchNotifications();
    } catch (err) {
      console.error('Lỗi cập nhật thông báo:', err);
    }
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  // ── Edit Folder/Document Functions ─────────────────────────────────────
  const handleOpenEdit = (id: string, type: 'folder' | 'document', name: string, description: string, tags: string[]) => {
    setEditTarget({ id, type, name, description, tags: (tags || []).join(', ') });
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editTarget) return;
    const tagsList = editTarget.tags.split(',').map(t => t.trim()).filter(t => t !== '');
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      if (editTarget.type === 'folder') {
        await axios.patch(`${API_BASE_URL}/folders/${editTarget.id}`, {
          name: editTarget.name,
          description: editTarget.description,
          tags: tagsList
        }, { headers });
      } else {
        await axios.patch(`${API_BASE_URL}/documents/${editTarget.id}`, {
          name: editTarget.name,
          description: editTarget.description,
          tags: tagsList
        }, { headers });
      }
      showNotification('Đã cập nhật thành công!');
      setEditTarget(null);
      fetchWorkspaceContent();
      if (showGroupDetail) {
        fetchGroupResources(showGroupDetail.id);
      }
    } catch (err: any) {
      showNotification(getErrorMessage(err, 'Lỗi cập nhật thông tin.'), true);
    }
  };

  // Local Sort & Filter logic
  const getProcessedItems = () => {
    let fList = [...folders];
    let dList = [...documents];

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      fList = fList.filter(f => f.name.toLowerCase().includes(q) || f.description.toLowerCase().includes(q));
      dList = dList.filter(d => d.name.toLowerCase().includes(q) || d.description.toLowerCase().includes(q));
    }

    if (selectedTag) {
      fList = fList.filter(f => f.tags && f.tags.includes(selectedTag));
      dList = dList.filter(d => d.tags && d.tags.includes(selectedTag));
    }

    if (sortBy === 'newest') {
      fList.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      dList.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    } else if (sortBy === 'oldest') {
      fList.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
      dList.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
    } else if (sortBy === 'alphabetical') {
      fList.sort((a, b) => a.name.localeCompare(b.name));
      dList.sort((a, b) => a.name.localeCompare(b.name));
    }

    return { fList, dList };
  };

  const { fList, dList } = getProcessedItems();
  const quotaPercent = Math.min(100, Math.round((quotaUsed * 100) / quotaLimit));

  // Compute all unique tags of current active folders and documents
  const allTags = Array.from(new Set([
    ...folders.flatMap(f => f.tags || []),
    ...documents.flatMap(d => d.tags || [])
  ]));

  return (
    <div className="app-container">
      {message && (
        <div className={`notification-toast ${message.isError ? 'error' : 'success'}`}>
          {message.text}
        </div>
      )}

      {!token ? (
        <div className="glass-card auth-card">
          <div className="logo-container">
            <div className="app-logo">{I.cloud}</div>
            <h2>CloudDocs</h2>
            <p className="app-subtitle">Hệ thống Quản lý và Cộng tác Tài liệu Học tập</p>
          </div>

          <div className="tab-buttons">
            <button
              className={`tab-btn ${isLoginTab ? 'active' : ''}`}
              onClick={() => setIsLoginTab(true)}
            >
              ĐĂNG NHẬP
            </button>
            <button
              className={`tab-btn ${!isLoginTab ? 'active' : ''}`}
              onClick={() => setIsLoginTab(false)}
            >
              ĐĂNG KÝ
            </button>
          </div>

          {isLoginTab ? (
            <form onSubmit={handleLogin} className="auth-form">
              <div className="input-group">
                <label>Email đăng nhập</label>
                <input
                  type="email"
                  placeholder="name@university.edu.vn"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div className="input-group">
                <label>Mật khẩu</label>
                <input
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              <button type="submit" className="submit-btn" disabled={loading}>
                {loading ? 'Đang xác thực...' : 'ĐĂNG NHẬP'}
              </button>
            </form>
          ) : (
            <form onSubmit={handleRegister} className="auth-form">
              <div className="input-group">
                <label>Họ và tên</label>
                <input
                  type="text"
                  placeholder="Nguyễn Văn A"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                />
              </div>
              <div className="input-group">
                <label>Email học tập</label>
                <input
                  type="email"
                  placeholder="name@university.edu.vn"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div className="input-group">
                <label>Mật khẩu (tối thiểu 8 ký tự)</label>
                <input
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              <button type="submit" className="submit-btn" disabled={loading}>
                {loading ? 'Đang tạo tài khoản...' : 'ĐĂNG KÝ'}
              </button>
            </form>
          )}
        </div>
      ) : (
        <div className="workspace-layout">
          {/* Sidebar */}
          <aside className={`sidebar ${sidebarOpen ? '' : 'collapsed'}`}>
            <div className="sidebar-header">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" className="logo-svg" style={{ marginRight: '10px', color: 'var(--accent-color)' }}><path d="M17.5 19A3.5 3.5 0 0 0 21 15.5c0-2.79-2.54-4.5-5-4.5-.42-3.1-2.74-5.5-6-5.5A5.5 5.5 0 0 0 4.5 11c-2.5 0-4.5 2-4.5 4.5A3.5 3.5 0 0 0 3.5 19z"></path></svg>
              <h3>CloudDocs</h3>
            </div>

            <nav className="sidebar-nav">
              <button
                className={`nav-item ${sidebarTab === 'files' ? 'active' : ''}`}
                onClick={() => { setSidebarTab('files'); setCurrentFolderId(null); setFolderPath([{ id: null, name: 'Trang chủ' }]); }}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" className="svg-icon" style={{ marginRight: '12px' }}><path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2z"></path></svg>
                Tài liệu của tôi
              </button>
              <button
                className={`nav-item ${sidebarTab === 'groups' ? 'active' : ''}`}
                onClick={() => setSidebarTab('groups')}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" className="svg-icon" style={{ marginRight: '12px' }}><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                Nhóm học tập
              </button>
              <button
                className={`nav-item ${sidebarTab === 'activities' ? 'active' : ''}`}
                onClick={() => setSidebarTab('activities')}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" className="svg-icon" style={{ marginRight: '12px' }}><rect x="3" y="4" width="18" height="16" rx="2"></rect><line x1="7" y1="8" x2="17" y2="8"></line><line x1="7" y1="12" x2="17" y2="12"></line><line x1="7" y1="16" x2="17" y2="16"></line></svg>
                Nhật ký hoạt động
              </button>
              <button
                className={`nav-item ${sidebarTab === 'trash' ? 'active' : ''}`}
                onClick={() => setSidebarTab('trash')}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" className="svg-icon" style={{ marginRight: '12px' }}><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                Thùng rác
              </button>
            </nav>

            {/* Storage Quota Ring Progress Bar */}
            <div className="quota-widget">
              <div className="quota-header">
                <span>Dung lượng lưu trữ</span>
                <span>{quotaPercent}%</span>
              </div>
              <div className="quota-bar">
                <div
                  className={`quota-fill ${quotaPercent > 85 ? 'danger' : quotaPercent > 60 ? 'warning' : 'success'}`}
                  style={{ width: `${quotaPercent}%` }}
                ></div>
              </div>
              <div className="quota-footer">
                {formatBytes(quotaUsed)} / {formatBytes(quotaLimit)}
              </div>
            </div>

            <div className="user-profile-section">
              <div className="avatar">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" className="svg-icon"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
              </div>
              <div className="user-info">
                <h4>{user?.full_name || 'Đang tải...'}</h4>
                <p>{user?.email}</p>
                <span className="badge-role">{user?.role}</span>
              </div>
              {/* Notification Bell */}
              <div className="notif-bell-container">
                <button className="notif-bell-btn" onClick={() => setShowNotifDropdown(!showNotifDropdown)} title="Thông báo" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" className="svg-icon"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
                  {unreadCount > 0 && <span className="notif-badge-count">{unreadCount}</span>}
                </button>
                {showNotifDropdown && (
                  <div className="notif-dropdown">
                    <div className="notif-dropdown-header" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" className="svg-icon" style={{ color: 'var(--accent-color)' }}><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
                      <h4 style={{ margin: 0 }}>Thông báo ({unreadCount} chưa đọc)</h4>
                      {unreadCount > 0 && (
                        <button className="btn-mark-all-read" onClick={handleMarkAllNotifsRead} style={{ marginLeft: 'auto' }}>Đọc tất cả</button>
                      )}
                    </div>
                    <div className="notif-dropdown-list">
                      {notifications.length === 0 ? (
                        <p className="no-notifs">Không có thông báo nào.</p>
                      ) : (
                        notifications.slice(0, 20).map(n => (
                          <div
                            className={`notif-item ${n.is_read ? 'read' : 'unread'}`}
                            key={n.id}
                            onClick={() => handleMarkNotifRead(n.id)}
                          >
                            <p className="notif-message">{n.message}</p>
                            <span className="notif-time">{formatUTCDate(n.created_at)}</span>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                )}
              </div>
              <button className="logout-icon-btn" onClick={handleLogout} title="Đăng xuất" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" className="svg-icon"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
              </button>
            </div>
          </aside>

          {/* Main workspace */}
          <main className="main-content" onDragEnter={handleDrag} onClick={() => setActiveMenuId(null)}>
            {/* Header / Breadcrumbs */}
            <header className="workspace-header">
              <div className="header-left">
                <button className="btn-toggle-sidebar" onClick={() => setSidebarOpen(!sidebarOpen)} title="Thu gọn/Mở rộng Sidebar">
                  {I.menu}
                </button>
                {sidebarTab === 'files' && folderPath.length > 1 && (
                  <button
                    className="btn-back-crumb"
                    onClick={() => navigateToBreadcrumb(folderPath.length - 2)}
                    title="Quay lại thư mục cấp trước"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>
                  </button>
                )}
                {sidebarTab === 'groups' && showGroupDetail && (
                  <button
                    className="btn-back-crumb"
                    onClick={() => setShowGroupDetail(null)}
                    title="Quay lại danh sách nhóm"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>
                  </button>
                )}
                <div className="breadcrumbs">
                  {sidebarTab === 'files' ? (
                    folderPath.map((path, idx) => (
                      <React.Fragment key={idx}>
                        <span
                          className={`crumb-item ${idx === folderPath.length - 1 ? 'active' : ''}`}
                          onClick={() => navigateToBreadcrumb(idx)}
                        >
                          {path.name}
                        </span>
                        {idx < folderPath.length - 1 && <span className="separator">/</span>}
                      </React.Fragment>
                    ))
                  ) : sidebarTab === 'activities' ? (
                    <span className="crumb-item active">Nhật ký thao tác hệ thống</span>
                  ) : sidebarTab === 'groups' ? (
                    showGroupDetail ? (
                      <>
                        <span className="crumb-item" onClick={() => setShowGroupDetail(null)}>Nhóm học tập của tôi</span>
                        <span className="separator">/</span>
                        <span className="crumb-item active">{showGroupDetail.name}</span>
                      </>
                    ) : (
                      <span className="crumb-item active">Nhóm học tập của tôi</span>
                    )
                  ) : (
                    <span className="crumb-item active">Thùng rác cá nhân</span>
                  )}
                </div>
              </div>

              {sidebarTab === 'files' && (
                <div className="action-buttons">
                  <button className="btn btn-secondary" onClick={() => setShowCreateFolder(true)}>
                    {I.folderPlus} Thư mục mới
                  </button>
                  <button className="btn btn-primary" onClick={() => fileInputRef.current?.click()}>
                    {I.upload} Tải file lên
                  </button>
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={(e) => handleSelectFile(e.target.files)}
                    style={{ display: 'none' }}
                  />
                </div>
              )}
              {sidebarTab === 'groups' && (
                <div className="action-buttons">
                  {showGroupDetail ? (
                    <>
                      <button className="btn btn-secondary" onClick={handleCreateGroupFolder}>
                        {I.folderPlus} Thư mục mới
                      </button>
                      <button className="btn btn-primary" onClick={() => groupFileInputRef.current?.click()}>
                        {I.upload} Tải file lên
                      </button>
                      <input
                        type="file"
                        ref={groupFileInputRef}
                        onChange={(e) => handleSelectFile(e.target.files)}
                        style={{ display: 'none' }}
                      />
                      <button 
                        className="btn-toggle-group-sidebar-right" 
                        onClick={() => setGroupSidebarOpen(!groupSidebarOpen)} 
                        title="Thu gọn/Mở rộng thông tin nhóm"
                      >
                        {I.menu}
                      </button>
                    </>
                  ) : (
                    <button className="btn btn-primary" onClick={() => setShowCreateGroup(true)}>
                      {I.usersPlus} Tạo nhóm mới
                    </button>
                  )}
                </div>
              )}
            </header>

            {/* Upload progress notifications */}
            {Object.keys(uploadProgress).map(filename => (
              <div className="upload-progress-bar-container" key={filename}>
                <div className="progress-info">
                  <span>Đang tải lên: {filename}</span>
                  <span>{uploadProgress[filename]}%</span>
                </div>
                <div className="bar">
                  <div className="fill" style={{ width: `${uploadProgress[filename]}%` }}></div>
                </div>
              </div>
            ))}

            {/* Search and Sort controls */}
            {sidebarTab === 'files' && (
              <div className="controls-row">
                <div className="search-box">
                  <span className="search-icon">{I.search}</span>
                  <input
                    type="text"
                    placeholder="Tìm kiếm tài liệu & thư mục..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                  {searchQuery && (
                    <button className="btn-clear-search" onClick={() => setSearchQuery('')}>×</button>
                  )}
                </div>

                <div className="sort-box">
                  <label>Sắp xếp:</label>
                  <select value={sortBy} onChange={(e: any) => setSortBy(e.target.value)}>
                    <option value="newest">Mới nhất</option>
                    <option value="oldest">Cũ nhất</option>
                    <option value="alphabetical">Tên A-Z</option>
                  </select>
                </div>
              </div>
            )}

            {/* Tags filter row */}
            {sidebarTab === 'files' && allTags.length > 0 && (
              <div className="tags-filter-bar">
                <span className="filter-title">Lọc theo nhãn:</span>
                <button
                  className={`tag-filter-btn ${!selectedTag ? 'active' : ''}`}
                  onClick={() => setSelectedTag(null)}
                >
                  Tất cả
                </button>
                {allTags.map(tag => (
                  <button
                    key={tag}
                    className={`tag-filter-btn ${selectedTag === tag ? 'active' : ''}`}
                    onClick={() => setSelectedTag(selectedTag === tag ? null : tag)}
                  >
                    #{tag}
                  </button>
                ))}
              </div>
            )}

            {/* Drag & drop overlay */}
            {dragActive && sidebarTab === 'files' && (
              <div
                className="drag-overlay"
                onDragEnter={handleDrag}
                onDragOver={handleDrag}
                onDragLeave={handleDrag}
                onDrop={handleDrop}
              >
                <div className="drop-zone">
                  <div className="drop-icon">{I.dropzone}</div>
                  <h3>Thả file vào đây để tự động tải lên</h3>
                  <p>Hỗ trợ tải lên tất cả các định dạng tệp tin.</p>
                </div>
              </div>
            )}

            {loading ? (
              <div className="spinner-loading">
                <div className="loader"></div>
                <p>Đang tải nội dung dữ liệu...</p>
              </div>
            ) : sidebarTab === 'files' ? (
              /* ACTIVE WORKSPACE VIEW */
              <div className="explorer-grid">
                {fList.length === 0 && dList.length === 0 && (
                  <div className="empty-state">
                    <div className="empty-icon">{I.inbox}</div>
                    <h3>Thư mục trống hoặc không có kết quả tìm kiếm</h3>
                    <p>Hãy kéo thả tệp tin hoặc bấm nút tải lên để lưu trữ tài liệu đầu tiên.</p>
                  </div>
                )}

                {/* Subfolders Section Header */}
                {fList.length > 0 && (
                  <div className="explorer-section-header" onClick={() => setFoldersExpanded(!foldersExpanded)}>
                    <span className="arrow-icon">{foldersExpanded ? '▼' : '▶'}</span>
                    {I.folder} Thư mục ({fList.length})
                  </div>
                )}

                {/* Subfolders list */}
                {foldersExpanded && fList.map(f => (
                  <div className={`explorer-item folder-item ${activeMenuId === `folder-${f.id}` ? 'has-open-menu' : ''}`} key={f.id} onDoubleClick={() => navigateToFolder(f)}>
                    <div className="item-icon">{I.folder}</div>
                    <div className="item-details">
                      <h4 className="item-name" title={f.name}>{f.name}</h4>
                      <p className="item-desc">{f.description || 'Không có mô tả'}</p>
                      {/* Subfolder tags */}
                      {f.tags && f.tags.length > 0 && (
                        <div className="item-tags-container">
                          {f.tags.map((t, idx) => (
                            <span key={idx} className="item-tag-badge" onClick={(e) => { e.stopPropagation(); setSelectedTag(t); }}>
                              #{t}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="item-actions-dropdown-container">
                      <button
                        className="btn-three-dots"
                        onClick={(e) => { e.stopPropagation(); setActiveMenuId(activeMenuId === `folder-${f.id}` ? null : `folder-${f.id}`); }}
                        title="Chức năng"
                      >
                        ⋮
                      </button>
                      {activeMenuId === `folder-${f.id}` && (
                        <div className="dropdown-menu glass-card" onClick={(e) => e.stopPropagation()}>
                          <button onClick={() => { setActiveMenuId(null); handleOpenEdit(f.id, 'folder', f.name, f.description, f.tags); }}>
                            {I.edit} Đổi tên / Mô tả / Nhãn
                          </button>
                          <button onClick={() => { setActiveMenuId(null); openShareModal(f.id, 'folder', f.name); }}>
                            {I.share} Chia sẻ
                          </button>
                          <button className="btn-delete" onClick={() => { setActiveMenuId(null); handleSoftDelete(f.id, 'folder'); }}>
                            {I.trash} Xóa thư mục
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {/* Documents Section Header */}
                {dList.length > 0 && (
                  <div className="explorer-section-header" onClick={() => setDocsExpanded(!docsExpanded)}>
                    <span className="arrow-icon">{docsExpanded ? '▼' : '▶'}</span>
                    {I.file} Tài liệu ({dList.length})
                  </div>
                )}

                {/* Documents list */}
                {docsExpanded && dList.map(doc => (
                  <div className={`explorer-item doc-item ${activeMenuId === `doc-${doc.id}` ? 'has-open-menu' : ''}`} key={doc.id}>
                    <div className="item-icon" onClick={() => handlePreviewDocument(doc)} title="Xem chi tiết & xem trước">
                      {doc.mime_type.includes('pdf') ? I.filePdf : doc.mime_type.includes('image') ? I.fileImage : I.file}
                    </div>
                    <div className="item-details" onClick={() => handlePreviewDocument(doc)}>
                      <h4 className="item-name" title={doc.name}>{doc.name}</h4>
                      <p className="item-desc">Phiên bản: v{doc.current_version} • {formatBytes(doc.file_size)}</p>
                      {/* Document tags */}
                      {doc.tags && doc.tags.length > 0 && (
                        <div className="item-tags-container">
                          {doc.tags.map((t, idx) => (
                            <span key={idx} className="item-tag-badge" onClick={(e) => { e.stopPropagation(); setSelectedTag(t); }}>
                              #{t}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="item-actions-dropdown-container">
                      <button
                        className="btn-three-dots"
                        onClick={(e) => { e.stopPropagation(); setActiveMenuId(activeMenuId === `doc-${doc.id}` ? null : `doc-${doc.id}`); }}
                        title="Chức năng"
                      >
                        ⋮
                      </button>
                      {activeMenuId === `doc-${doc.id}` && (
                        <div className="dropdown-menu glass-card" onClick={(e) => e.stopPropagation()}>
                          <button onClick={() => { setActiveMenuId(null); handleOpenEdit(doc.id, 'document', doc.name, doc.description, doc.tags); }}>
                            {I.edit} Sửa tên / Nhãn / Mô tả
                          </button>
                          <button onClick={() => { setActiveMenuId(null); handleDownloadFile(doc); }}>
                            {I.download} Tải xuống
                          </button>
                          <button onClick={() => { setActiveMenuId(null); openHistoryDrawer(doc); }}>
                            {I.clock} Lịch sử phiên bản
                          </button>
                          <button onClick={() => { setActiveMenuId(null); openShareModal(doc.id, 'document', doc.name); }}>
                            {I.share} Chia sẻ tài liệu
                          </button>
                          <button className="btn-delete" onClick={() => { setActiveMenuId(null); handleSoftDelete(doc.id, 'document'); }}>
                            {I.trash} Xóa tài liệu
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : sidebarTab === 'activities' ? (
              /* ACTIVITIES LOG VIEW */
              <div className="activities-log-view">
                {activitiesList.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-icon">{I.inbox}</div>
                    <h3>Chưa có nhật ký hoạt động nào</h3>
                  </div>
                ) : (
                  <div className="activities-table-container">
                    <table className="activities-table">
                      <thead>
                        <tr>
                          <th>Thời gian</th>
                          <th>Người thực hiện</th>
                          <th>Hành động</th>
                          <th>Tài nguyên</th>
                          <th>Chi tiết</th>
                        </tr>
                      </thead>
                      <tbody>
                        {activitiesList.map(act => (
                          <tr key={act.id}>
                            <td>{formatUTCDate(act.created_at)}</td>
                            <td className="col-user">{act.user_name}</td>
                            <td>
                              <span className={`act-tag ${act.action.toLowerCase()}`}>
                                {act.action}
                              </span>
                            </td>
                            <td className="col-resource">{act.resource_name}</td>
                            <td>{act.details}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            ) : sidebarTab === 'groups' ? (
              /* STUDY GROUPS VIEW */
              showGroupDetail ? (
                <div className="group-workspace-layout">
                  {/* Left Column: File Explorer */}
                  <div className="group-workspace-main">
                    {loadingGroupResources ? (
                      <p className="loading-text">Đang tải tài nguyên của nhóm...</p>
                    ) : (
                      <div className="explorer-grid">
                        {/* Section: Folders */}
                        <div className="explorer-section-header" onClick={() => setFoldersExpanded(!foldersExpanded)}>
                          <span className="arrow-icon">{foldersExpanded ? '▼' : '▶'}</span>
                          {I.folder} Thư mục nhóm ({groupFolders.length})
                        </div>
                        {foldersExpanded && groupFolders.length > 0 && (
                          groupFolders.map(f => (
                            <div
                              className={`explorer-item folder-item ${activeMenuId === `gfolder-${f.id}` ? 'has-open-menu' : ''}`}
                              key={f.id}
                              onDoubleClick={() => {
                                setSidebarTab('files');
                                setFolderPath([
                                  { id: null, name: 'Nhóm học tập của tôi' },
                                  { id: 'GROUP_ROOT', name: showGroupDetail.name, isGroupRoot: true, group: showGroupDetail },
                                  { id: f.id, name: f.name }
                                ]);
                                setCurrentFolderId(f.id);
                                setShowGroupDetail(null);
                              }}
                              title="Click đúp để mở thư mục này"
                            >
                              <div className="item-icon">{I.folder}</div>
                              <div className="item-details">
                                <h4 className="item-name" title={f.name}>{f.name}</h4>
                                <p className="item-desc">{f.description || 'Thư mục nhóm'}</p>
                                {f.tags && f.tags.length > 0 && (
                                  <div className="item-tags-container">
                                    {f.tags.map((t, idx) => (
                                      <span key={idx} className="item-tag-badge" onClick={(e) => { e.stopPropagation(); setSelectedTag(t); }}>
                                        #{t}
                                      </span>
                                    ))}
                                  </div>
                                )}
                              </div>
                              <div className="item-actions-dropdown-container">
                                <button
                                  className="btn-three-dots"
                                  onClick={(e) => { e.stopPropagation(); setActiveMenuId(activeMenuId === `gfolder-${f.id}` ? null : `gfolder-${f.id}`); }}
                                  title="Chức năng"
                                >
                                  ⋮
                                </button>
                                {activeMenuId === `gfolder-${f.id}` && (
                                  <div className="dropdown-menu glass-card" onClick={(e) => e.stopPropagation()}>
                                    <button onClick={() => { setActiveMenuId(null); handleOpenEdit(f.id, 'folder', f.name, f.description, f.tags); }}>
                                      {I.edit} Đổi tên / Mô tả / Nhãn
                                    </button>
                                    <button onClick={() => { setActiveMenuId(null); openShareModal(f.id, 'folder', f.name); }}>
                                      {I.share} Chia sẻ
                                    </button>
                                    <button className="btn-delete" onClick={() => { setActiveMenuId(null); handleSoftDelete(f.id, 'folder'); }}>
                                      {I.trash} Xóa thư mục
                                    </button>
                                  </div>
                                )}
                              </div>
                            </div>
                          ))
                        )}

                        {/* Section: Documents */}
                        <div className="explorer-section-header" onClick={() => setDocsExpanded(!docsExpanded)}>
                          <span className="arrow-icon">{docsExpanded ? '▼' : '▶'}</span>
                          {I.file} Tài liệu nhóm ({groupDocs.length})
                        </div>
                        {docsExpanded && groupDocs.length > 0 && (
                          groupDocs.map(doc => (
                            <div
                              className={`explorer-item doc-item ${activeMenuId === `gdoc-${doc.id}` ? 'has-open-menu' : ''}`}
                              key={doc.id}
                            >
                              <div className="item-icon" onClick={() => handlePreviewDocument(doc)} title="Xem chi tiết & bình luận">
                                {doc.mime_type.includes('pdf') ? I.filePdf : doc.mime_type.includes('image') ? I.fileImage : I.file}
                              </div>
                              <div className="item-details" onClick={() => handlePreviewDocument(doc)}>
                                <h4 className="item-name" title={doc.name}>{doc.name}</h4>
                                <p className="item-desc">Phiên bản: v{doc.current_version || 1} • {formatBytes(doc.file_size)}</p>
                                {doc.tags && doc.tags.length > 0 && (
                                  <div className="item-tags-container">
                                    {doc.tags.map((t, idx) => (
                                      <span key={idx} className="item-tag-badge" onClick={(e) => { e.stopPropagation(); setSelectedTag(t); }}>
                                        #{t}
                                      </span>
                                    ))}
                                  </div>
                                )}
                              </div>
                              <div className="item-actions-dropdown-container">
                                <button
                                  className="btn-three-dots"
                                  onClick={(e) => { e.stopPropagation(); setActiveMenuId(activeMenuId === `gdoc-${doc.id}` ? null : `gdoc-${doc.id}`); }}
                                  title="Chức năng"
                                >
                                  ⋮
                                </button>
                                {activeMenuId === `gdoc-${doc.id}` && (
                                  <div className="dropdown-menu glass-card" onClick={(e) => e.stopPropagation()}>
                                    <button onClick={() => { setActiveMenuId(null); handleOpenEdit(doc.id, 'document', doc.name, doc.description, doc.tags); }}>
                                      {I.edit} Sửa tên / Nhãn / Mô tả
                                    </button>
                                    <button onClick={() => { setActiveMenuId(null); handleDownloadFile(doc); }}>
                                      {I.download} Tải xuống
                                    </button>
                                    <button onClick={() => { setActiveMenuId(null); openHistoryDrawer(doc); }}>
                                      {I.clock} Lịch sử phiên bản
                                    </button>
                                    <button onClick={() => { setActiveMenuId(null); openShareModal(doc.id, 'document', doc.name); }}>
                                      {I.share} Chia sẻ tài liệu
                                    </button>
                                    <button className="btn-delete" onClick={() => { setActiveMenuId(null); handleSoftDelete(doc.id, 'document'); }}>
                                      {I.trash} Xóa tài liệu
                                    </button>
                                  </div>
                                )}
                              </div>
                            </div>
                          ))
                        )}

                        {groupFolders.length === 0 && groupDocs.length === 0 && (
                          <div className="empty-state" style={{ gridColumn: '1 / -1' }}>
                            <div className="empty-icon">{I.inbox}</div>
                            <h3>Chưa có tài liệu hay thư mục nào</h3>
                            <p>Sử dụng các nút bên trên để tạo thư mục mới hoặc tải lên tài liệu đầu tiên cho nhóm nhé!</p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Right Column: Group Info Sidebar */}
                  {groupSidebarOpen && (
                    <div className="group-workspace-sidebar glass-card">
                      <div className="group-info-header">
                        <h3>{I.users} {showGroupDetail.name}</h3>
                        <p className="group-workspace-desc">{showGroupDetail.description || 'Không có mô tả'}</p>
                      </div>

                      {/* Invite Link */}
                      <div className="group-sidebar-card">
                        <label className="sidebar-section-label">{I.link} Link mời vào nhóm:</label>
                        <div className="sidebar-input-row">
                          <input
                            type="text"
                            readOnly
                            value={`${window.location.origin}/join/${showGroupDetail.invite_code || ''}`}
                            className="sidebar-input-field"
                          />
                          <button
                            type="button"
                            className="btn btn-primary btn-copy-link"
                            onClick={() => handleCopyInviteLink(showGroupDetail.invite_code || '')}
                          >
                            {I.copy} Sao chép
                          </button>
                        </div>
                      </div>

                      {/* Invite Email Form */}
                      <form onSubmit={handleInviteMember} className="group-sidebar-card">
                        <label className="sidebar-section-label">{I.mail} Mời qua email:</label>
                        <div className="sidebar-input-row">
                          <input
                            type="email"
                            placeholder="Nhập email thành viên..."
                            value={inviteMemberEmail}
                            onChange={(e) => setInviteMemberEmail(e.target.value)}
                            className="sidebar-input-field"
                            required
                          />
                          <button type="submit" className="btn btn-primary btn-invite-submit">
                            Mời
                          </button>
                        </div>
                      </form>

                      {/* Pending Requests for Owners */}
                      {user && user.id === showGroupDetail.created_by && (
                        <div className="group-sidebar-card">
                          <label className="sidebar-section-label">{I.clock} Yêu cầu chờ phê duyệt ({showGroupDetail.pending_members?.length || 0}):</label>
                          {!showGroupDetail.pending_members || showGroupDetail.pending_members.length === 0 ? (
                            <p className="no-pending-requests">Không có yêu cầu nào.</p>
                          ) : (
                            showGroupDetail.pending_members.map((pm, idx) => (
                              <div className="collab-item pending-item" key={idx}>
                                <div className="collab-info">
                                  <span className="collab-email" title={pm.email}>
                                    {pm.full_name ? `${pm.full_name} (${pm.email})` : pm.email}
                                  </span>
                                </div>
                                <div className="pending-actions">
                                  <button
                                    type="button"
                                    className="btn btn-success btn-approve"
                                    onClick={() => handleApproveRequest(showGroupDetail.id, pm.user_id)}
                                    title="Đồng ý"
                                  >
                                    ✓
                                  </button>
                                  <button
                                    type="button"
                                    className="btn btn-danger btn-reject"
                                    onClick={() => handleRejectRequest(showGroupDetail.id, pm.user_id)}
                                    title="Từ chối"
                                  >
                                    ✗
                                  </button>
                                </div>
                              </div>
                            ))
                          )}
                        </div>
                      )}

                      {/* Members List */}
                      <div className="group-sidebar-card">
                        <label className="sidebar-section-label">{I.users} Thành viên ({showGroupDetail.members.length}):</label>
                        <div className="members-scroll">
                          {showGroupDetail.members.map((member, idx) => (
                            <div className="group-member-row" key={idx}>
                              <div className="collab-info">
                                <span className="collab-name">{member.full_name || 'Thành viên'}</span>
                                <span className="collab-email">{member.email}</span>
                              </div>
                              {member.id === showGroupDetail.created_by && (
                                <span className="owner-badge">Chủ nhóm</span>
                              )}
                              {member.id !== showGroupDetail.created_by && user && member.id !== user.id && (
                                <button type="button" className="btn-remove-collab" onClick={() => handleRemoveMember(member.id)} title="Xóa thành viên">
                                  ✕
                                </button>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="explorer-grid groups-grid">
                  {groups.length === 0 ? (
                    <div className="empty-state">
                      <div className="empty-icon">{I.users}</div>
                      <h3>Bạn chưa tham gia nhóm học tập nào</h3>
                      <p>Bấm "+ Tạo nhóm mới" để bắt đầu cộng tác cùng bạn bè!</p>
                    </div>
                  ) : (
                    groups.map(g => (
                      <div className={`explorer-item group-item ${activeMenuId === `group-${g.id}` ? 'has-open-menu' : ''}`} key={g.id} onClick={() => setShowGroupDetail(g)}>
                        <div className="item-icon">{I.users}</div>
                        <div className="item-details">
                          <h4 className="item-name">{g.name}</h4>
                          <p className="item-desc">{g.description || 'Không có mô tả'}</p>
                          <span className="group-member-count">{g.members.length} thành viên</span>
                        </div>
                        <div className="item-actions-dropdown-container">
                          <button
                            className="btn-three-dots"
                            onClick={(e) => { e.stopPropagation(); setActiveMenuId(activeMenuId === `group-${g.id}` ? null : `group-${g.id}`); }}
                            title="Chức năng nhóm"
                          >
                            ⋮
                          </button>
                          {activeMenuId === `group-${g.id}` && (
                            <div className="dropdown-menu glass-card" onClick={(e) => e.stopPropagation()}>
                              <button onClick={() => { setActiveMenuId(null); handleOpenEditGroup(g); }}>
                                {I.edit} Sửa thông tin nhóm
                              </button>
                              <button className="btn-delete" onClick={() => { setActiveMenuId(null); handleDeleteGroup(g.id, g.name); }}>
                                {I.trash} Xóa nhóm học tập
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    ))
                  )}

                  {/* Form tham gia nhóm qua link mời */}
                  <div className="join-via-link-section">
                    <h4>{I.link} Tham gia nhóm qua link mời</h4>
                    <form onSubmit={handleJoinViaLink} className="join-link-form">
                      <input
                        type="text"
                        placeholder="Dán link mời hoặc mã mời vào đây..."
                        value={joinInviteCode}
                        onChange={(e) => setJoinInviteCode(e.target.value)}
                        required
                      />
                      <button type="submit" className="btn btn-primary">Tham gia</button>
                    </form>
                  </div>
                </div>
              )
            ) : (
              /* TRASH VIEW */
              <div className="explorer-grid">
                {trashFolders.length === 0 && trashDocuments.length === 0 && (
                  <div className="empty-state">
                    <div className="empty-icon">{I.trash}</div>
                    <h3>Thùng rác trống</h3>
                    <p>Các tài nguyên bị xóa mềm sẽ hiển thị tại đây.</p>
                  </div>
                )}

                {/* Trash folders */}
                {trashFolders.map(f => (
                  <div className="explorer-item folder-item trash-item" key={f.id}>
                    <div className="item-icon">{I.folder}</div>
                    <div className="item-details">
                      <h4 className="item-name">{f.name}</h4>
                      <p className="item-desc">Đã xóa mềm</p>
                    </div>
                    <div className="item-actions">
                      <button className="btn-restore" onClick={() => handleRestore(f.id, 'folder')} title="Khôi phục">{I.undo} Khôi phục</button>
                    </div>
                  </div>
                ))}

                {/* Trash documents */}
                {trashDocuments.map(doc => (
                  <div className="explorer-item doc-item trash-item" key={doc.id}>
                    <div className="item-icon">{I.file}</div>
                    <div className="item-details">
                      <h4 className="item-name">{doc.name}</h4>
                      <p className="item-desc">Cỡ: {formatBytes(doc.file_size)}</p>
                    </div>
                    <div className="item-actions">
                      <button className="btn-restore" onClick={() => handleRestore(doc.id, 'document')} title="Khôi phục">{I.undo} Khôi phục</button>
                      <button className="btn-delete-forever" onClick={() => handleHardDelete(doc.id, 'document')} title="Xóa vĩnh viễn">{I.trash} Xóa cứng</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </main>

          {/* Modal Tạo thư mục mới */}
          {showCreateFolder && (
            <div className="modal-backdrop">
              <div className="modal-content glass-card">
                <h3>{I.folderPlus} Tạo thư mục mới</h3>
                <form onSubmit={handleCreateFolder}>
                  <div className="input-group">
                    <label>Tên thư mục</label>
                    <input
                      type="text"
                      placeholder="Nhập tên thư mục..."
                      value={newFolderName}
                      onChange={(e) => setNewFolderName(e.target.value)}
                      required
                    />
                  </div>
                  <div className="input-group">
                    <label>Mô tả ngắn</label>
                    <input
                      type="text"
                      placeholder="Mô tả thư mục..."
                      value={newFolderDesc}
                      onChange={(e) => setNewFolderDesc(e.target.value)}
                    />
                  </div>
                  <div className="input-group">
                    <label>Thẻ nhãn / Môn học (phân cách bằng dấu phẩy)</label>
                    <input
                      type="text"
                      placeholder="Ví dụ: Lập trình, Python, Kỳ 1"
                      value={newFolderTags}
                      onChange={(e) => setNewFolderTags(e.target.value)}
                    />
                  </div>
                  <div className="modal-actions">
                    <button type="button" className="btn btn-secondary" onClick={() => setShowCreateFolder(false)}>
                      Hủy bỏ
                    </button>
                    <button type="submit" className="btn btn-primary">
                      Tạo ngay
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {/* Modal Tải tài liệu lên kèm nhãn dán */}
          {uploadFileObj && (
            <div className="modal-backdrop">
              <div className="modal-content glass-card">
                <h3>{I.upload} Tải tài liệu mới lên</h3>
                <p className="upload-filename-preview">Kích thước tệp: <strong>{formatBytes(uploadFileObj.size)}</strong></p>
                <form onSubmit={executeUploadFile}>
                  <div className="input-group">
                    <label>Tên tài liệu / Tệp tin</label>
                    <input
                      type="text"
                      placeholder="Nhập tên tệp tin mong muốn..."
                      value={uploadFileName}
                      onChange={(e) => setUploadFileName(e.target.value)}
                      required
                    />
                  </div>
                  <div className="input-group">
                    <label>Mô tả tài liệu</label>
                    <input
                      type="text"
                      placeholder="Nhập mô tả về tài liệu này..."
                      value={uploadDescription}
                      onChange={(e) => setUploadDescription(e.target.value)}
                    />
                  </div>
                  <div className="input-group">
                    <label>Thẻ nhãn dán / Phân loại (phân cách bằng dấu phẩy)</label>
                    <input
                      type="text"
                      placeholder="Ví dụ: Đại số, Bài tập, Giáo trình"
                      value={uploadTags}
                      onChange={(e) => setUploadTags(e.target.value)}
                    />
                  </div>
                  <div className="modal-actions">
                    <button type="button" className="btn btn-secondary" onClick={() => setUploadFileObj(null)}>
                      Hủy bỏ
                    </button>
                    <button type="submit" className="btn btn-primary">
                      Tải lên ngay
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {/* Modal Chia sẻ Phân quyền (ACL Share) */}
          {showShareModal && (
            <div className="modal-backdrop">
              <div className="modal-content glass-card share-modal">
                <h3>{I.share} Chia sẻ quyền truy cập</h3>
                <p className="share-target-name">Tài nguyên: <strong>{showShareModal.name}</strong></p>

                {/* Toggle Share Type */}
                <div className="share-type-toggle">
                  <button className={`toggle-btn ${shareType === 'user' ? 'active' : ''}`} onClick={() => setShareType('user')}>
                    {I.user} Cá nhân
                  </button>
                  <button className={`toggle-btn ${shareType === 'group' ? 'active' : ''}`} onClick={() => setShareType('group')}>
                    {I.users} Nhóm học tập
                  </button>
                </div>

                <form onSubmit={async (e) => {
                  e.preventDefault();
                  if (!showShareModal) return;
                  try {
                    const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
                    const payload: any = {
                      resource_id: showShareModal.id,
                      resource_type: showShareModal.type,
                      access_level: shareLevel,
                      share_type: shareType
                    };
                    if (shareType === 'user') {
                      if (!shareEmail.trim()) return;
                      payload.user_email = shareEmail;
                    } else {
                      if (!shareGroupId) return;
                      payload.group_id = shareGroupId;
                    }
                    await axios.post(`${API_BASE_URL}/permissions`, payload, { headers });
                    showNotification('Đã chia sẻ quyền truy cập thành công!');
                    setShareEmail('');
                    setShareGroupId('');
                    const res = await axios.get(`${API_BASE_URL}/permissions/${showShareModal.type}/${showShareModal.id}`, { headers });
                    setCollaborators(res.data);
                    fetchNotifications();
                  } catch (err: any) {
                    showNotification(getErrorMessage(err, 'Lỗi chia sẻ tài nguyên.'), true);
                  }
                }} className="share-form">
                  <div className="share-inputs">
                    {shareType === 'user' ? (
                      <input
                        type="email"
                        placeholder="Nhập email bạn học (cộng tác viên)..."
                        value={shareEmail}
                        onChange={(e) => setShareEmail(e.target.value)}
                        required
                      />
                    ) : (
                      <select value={shareGroupId} onChange={(e) => setShareGroupId(e.target.value)} required>
                        <option value="">-- Chọn nhóm học tập --</option>
                        {groups.map(g => (
                          <option key={g.id} value={g.id}>{g.name} ({g.members.length} TV)</option>
                        ))}
                      </select>
                    )}
                    <select value={shareLevel} onChange={(e: any) => setShareLevel(e.target.value)}>
                      <option value="viewer">Viewer (Chỉ xem)</option>
                      <option value="editor">Editor (Có quyền sửa)</option>
                    </select>
                    <button type="submit" className="btn btn-primary">Chia sẻ</button>
                  </div>
                </form>

                <div className="collaborators-list">
                  <h4>Danh sách cộng tác viên đang chia sẻ:</h4>
                  {collaborators.length === 0 ? (
                    <p className="no-collaborators">Tài nguyên này chưa chia sẻ cho ai.</p>
                  ) : (
                    collaborators.map(c => (
                      <div className="collab-item" key={c.id}>
                        <div className="collab-info">
                          <span className="collab-email">
                            {c.share_type === 'group' ? `Nhóm: ${c.group_name || 'Nhóm'}` : `${c.user_email}`}
                          </span>
                          <span className="collab-role-tag">{c.access_level}</span>
                          <span className="collab-share-type-badge">{c.share_type === 'group' ? 'Nhóm' : 'Cá nhân'}</span>
                        </div>
                        <button className="btn-remove-collab" onClick={() => handleRevokeShare(c.id)} title="Thu hồi chia sẻ">
                          ❌
                        </button>
                      </div>
                    ))
                  )}
                </div>

                {/* Chia sẻ qua liên kết (General Link Access - tương tự Google Drive) */}
                <div className="link-sharing-section">
                  <h4>🌐 Quyền truy cập chung (Chia sẻ qua liên kết)</h4>
                  <div className="link-sharing-control">
                    <div className="link-sharing-row">
                      <select
                        value={shareLinkAccess}
                        onChange={(e) => {
                          const val = e.target.value as 'restricted' | 'anyone';
                          setShareLinkAccess(val);
                          handleUpdateLinkSharing(val, shareLinkLevel);
                        }}
                        className="select-link-access"
                      >
                        <option value="restricted">Hạn chế (Chỉ người được mời)</option>
                        <option value="anyone">Bất kỳ ai có liên kết</option>
                      </select>

                      {shareLinkAccess === 'anyone' && (
                        <select
                          value={shareLinkLevel}
                          onChange={(e) => {
                            const val = e.target.value as 'viewer' | 'editor';
                            setShareLinkLevel(val);
                            handleUpdateLinkSharing(shareLinkAccess, val);
                          }}
                          className="select-link-level"
                        >
                          <option value="viewer">Viewer (Chỉ xem)</option>
                          <option value="editor">Editor (Có quyền sửa)</option>
                        </select>
                      )}
                    </div>

                    {shareLinkAccess === 'anyone' && (
                      <div className="share-link-copy-container">
                        <input
                          type="text"
                          readOnly
                          value={`${window.location.origin}/?previewDoc=${showShareModal.id}`}
                          className="share-link-url"
                        />
                        <button
                          className="btn btn-primary btn-copy-share-link"
                          onClick={() => {
                            const link = `${window.location.origin}/?previewDoc=${showShareModal.id}`;
                            navigator.clipboard.writeText(link).then(() => {
                              showNotification('Đã sao chép liên kết chia sẻ!');
                            }).catch(() => {
                              window.prompt('Sao chép liên kết bên dưới:', link);
                            });
                          }}
                        >
                          {I.copy} Sao chép
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                <div className="modal-actions">
                  <button className="btn btn-secondary" onClick={() => { setShowShareModal(null); setShareType('user'); }}>
                    Đóng lại
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Drawer Lịch sử Phiên bản (Version History) */}
          {showHistoryDrawer && (
            <div className="drawer-backdrop" onClick={() => setShowHistoryDrawer(null)}>
              <div className="drawer-content glass-card" onClick={(e) => e.stopPropagation()}>
                <div className="drawer-header">
                  <h3>{I.clock} Lịch sử phiên bản</h3>
                  <button className="btn-close-drawer" onClick={() => setShowHistoryDrawer(null)}>{I.x}</button>
                </div>

                <p className="drawer-subtitle">File: <strong>{showHistoryDrawer.name}</strong></p>

                {/* Form upload version mới */}
                <div className="upload-new-version-section">
                  <h4>{I.upload} Tải lên phiên bản mới</h4>
                  <input
                    type="text"
                    placeholder="Ghi chú các thay đổi phiên bản này..."
                    value={versionChangeLog}
                    onChange={(e) => setVersionChangeLog(e.target.value)}
                  />
                  <button className="btn btn-primary" onClick={() => newVersionInputRef.current?.click()}>
                    Chọn File & Upload Version Mới
                  </button>
                  <input
                    type="file"
                    ref={newVersionInputRef}
                    onChange={(e) => handleUploadNewVersion(e.target.files)}
                    style={{ display: 'none' }}
                  />
                </div>

                <div className="versions-timeline">
                  <h4>Dòng thời gian các phiên bản:</h4>
                  {versions.length === 0 ? (
                    <p className="no-versions">Đang tải lịch sử...</p>
                  ) : (
                    versions.map(v => (
                      <div className="version-timeline-item" key={v.id}>
                        <div className="version-marker">v{v.version_number}</div>
                        <div className="version-meta">
                          <p className="version-log">"{v.change_log || 'Không có ghi chú'}"</p>
                          <span className="version-date">{formatUTCDate(v.created_at)}</span>
                          <span className="version-size"> • Cỡ: {formatBytes(v.file_size)}</span>
                        </div>
                        <button className="btn btn-secondary btn-rollback" onClick={() => handleRollback(v.version_number)}>
                          {I.undo} Khôi phục v{v.version_number}
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Drawer Xem trước Tài liệu & Bình luận (Doc Preview & Comments) */}
          {previewDoc && (
            <div className="modal-backdrop" onClick={() => setPreviewDoc(null)}>
              <div className="preview-drawer-content glass-card" onClick={(e) => e.stopPropagation()}>
                <div className="preview-drawer-left">
                  <div className="preview-header">
                    <h2>{I.eye} Xem trước tài liệu</h2>
                    <span className="file-preview-name">{previewDoc.doc.name}</span>
                  </div>

                  <div className="preview-viewport">
                    {previewDoc.doc.mime_type.includes('pdf') ? (
                      <iframe
                        src={previewDoc.presignedUrl}
                        width="100%"
                        height="100%"
                        title="PDF Preview"
                        style={{ border: 'none', borderRadius: '12px' }}
                      ></iframe>
                    ) : previewDoc.doc.mime_type.includes('image') ? (
                      <div className="image-preview-container">
                        <img src={previewDoc.presignedUrl} alt="Preview" />
                      </div>
                    ) : (
                      previewDoc.doc.mime_type.includes('word') ||
                      previewDoc.doc.mime_type.includes('document') ||
                      previewDoc.doc.mime_type.includes('spreadsheet') ||
                      previewDoc.doc.mime_type.includes('presentation') ||
                      previewDoc.doc.mime_type.includes('excel') ||
                      previewDoc.doc.mime_type.includes('msword') ||
                      previewDoc.doc.name.endsWith('.docx') ||
                      previewDoc.doc.name.endsWith('.doc') ||
                      previewDoc.doc.name.endsWith('.xlsx') ||
                      previewDoc.doc.name.endsWith('.pptx')
                    ) ? (
                      <iframe
                        src={`https://view.officeapps.live.com/op/embed.aspx?src=${encodeURIComponent(previewDoc.presignedUrl)}`}
                        width="100%"
                        height="100%"
                        title="Office Document Preview"
                        style={{ border: 'none', borderRadius: '12px' }}
                      ></iframe>
                    ) : (
                      <div className="generic-preview">
                        <span className="preview-file-icon">{I.file}</span>
                        <h4>Định dạng file không hỗ trợ xem trước trên web</h4>
                        <p>Định dạng: {previewDoc.doc.mime_type}</p>
                        <button className="btn btn-primary" onClick={() => handleDownloadFile(previewDoc.doc)}>
                          {I.download} Tải tài liệu về máy
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                <div className="preview-drawer-right">
                  <div className="drawer-header">
                    <h3>{I.comment} Bình luận / Ghi chú</h3>
                    <button className="btn-close-drawer" onClick={() => setPreviewDoc(null)}>{I.x}</button>
                  </div>

                  <div className="comments-timeline">
                    {comments.length === 0 ? (
                      <p className="no-comments">Chưa có bình luận nào. Hãy bắt đầu thảo luận!</p>
                    ) : (
                      comments.map(c => (
                        <div className="comment-bubble-item" key={c.id}>
                          <div className="comment-author-info">
                            <strong>{c.user_name}</strong>
                            <span className="comment-date">{new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                          </div>
                          <p className="comment-content-text">{c.content}</p>
                        </div>
                      ))
                    )}
                  </div>

                  <form onSubmit={handleAddComment} className="comment-input-form">
                    <input
                      type="text"
                      placeholder="Viết ghi chú hoặc thảo luận..."
                      value={newComment}
                      onChange={(e) => setNewComment(e.target.value)}
                      required
                    />
                    <button type="submit" className="btn btn-primary">Gửi</button>
                  </form>
                </div>
              </div>
            </div>
          )}

          {/* Modal Tạo nhóm học tập mới */}
          {showCreateGroup && (
            <div className="modal-backdrop">
              <div className="modal-content glass-card">
                <h3>{I.usersPlus} Tạo nhóm học tập mới</h3>
                <form onSubmit={handleCreateGroup}>
                  <div className="input-group">
                    <label>Tên nhóm</label>
                    <input
                      type="text"
                      placeholder="Nhập tên nhóm học tập..."
                      value={newGroupName}
                      onChange={(e) => setNewGroupName(e.target.value)}
                      required
                    />
                  </div>
                  <div className="input-group">
                    <label>Mô tả nhóm</label>
                    <input
                      type="text"
                      placeholder="Mô tả ngắn gọn nhóm học tập..."
                      value={newGroupDesc}
                      onChange={(e) => setNewGroupDesc(e.target.value)}
                    />
                  </div>
                  <div className="modal-actions">
                    <button type="button" className="btn btn-secondary" onClick={() => setShowCreateGroup(false)}>Hủy bỏ</button>
                    <button type="submit" className="btn btn-primary">Tạo nhóm</button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {/* Modal Sửa đổi thông tin Folder/Document */}
          {editTarget && (
            <div className="modal-backdrop">
              <div className="modal-content glass-card">
                <h3>{I.edit} Chỉnh sửa thông tin {editTarget.type === 'folder' ? 'Thư mục' : 'Tài liệu'}</h3>
                <form onSubmit={handleSaveEdit}>
                  <div className="input-group">
                    <label>Tên {editTarget.type === 'folder' ? 'thư mục' : 'tài liệu'}</label>
                    <input
                      type="text"
                      value={editTarget.name}
                      onChange={(e) => setEditTarget({ ...editTarget, name: e.target.value })}
                      required
                    />
                  </div>
                  <div className="input-group">
                    <label>Mô tả</label>
                    <input
                      type="text"
                      value={editTarget.description}
                      onChange={(e) => setEditTarget({ ...editTarget, description: e.target.value })}
                    />
                  </div>
                  <div className="input-group">
                    <label>Thẻ nhãn (phân cách bằng dấu phẩy)</label>
                    <input
                      type="text"
                      value={editTarget.tags}
                      onChange={(e) => setEditTarget({ ...editTarget, tags: e.target.value })}
                    />
                  </div>
                  <div className="modal-actions">
                    <button type="button" className="btn btn-secondary" onClick={() => setEditTarget(null)}>Hủy bỏ</button>
                    <button type="submit" className="btn btn-primary">Lưu thay đổi</button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {/* Modal Sửa đổi thông tin Nhóm học tập */}
          {editGroupTarget && (
            <div className="modal-backdrop">
              <div className="modal-content glass-card">
                <h3>{I.edit} Chỉnh sửa thông tin Nhóm học tập</h3>
                <form onSubmit={handleSaveEditGroup}>
                  <div className="input-group">
                    <label>Tên nhóm học tập</label>
                    <input
                      type="text"
                      value={editGroupTarget.name}
                      onChange={(e) => setEditGroupTarget({ ...editGroupTarget, name: e.target.value })}
                      required
                    />
                  </div>
                  <div className="input-group">
                    <label>Mô tả nhóm</label>
                    <input
                      type="text"
                      value={editGroupTarget.description}
                      onChange={(e) => setEditGroupTarget({ ...editGroupTarget, description: e.target.value })}
                    />
                  </div>
                  <div className="modal-actions">
                    <button type="button" className="btn btn-secondary" onClick={() => setEditGroupTarget(null)}>Hủy bỏ</button>
                    <button type="submit" className="btn btn-primary">Lưu thay đổi</button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
