import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  getCurrentUser,
  updateUserProfile,
  changePassword,
  exportUserData,
  deleteAccount,
} from '@/lib/api';
import { useAuthStore } from '@/features/auth/authStore';
import Icon from '@/components/common/Icon';
import { toast } from '@/components/common/toastStore';

/**
 * Candidate Profile and Settings view.
 * Handles profile preferences, target companies, password updates,
 * complete JSON data export, and account deletion.
 */
export const ProfilePage = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { user: authUser, setUser, logout } = useAuthStore();

  const { data: user, refetch } = useQuery({
    queryKey: ['users-me'],
    queryFn: getCurrentUser,
    initialData: authUser || undefined,
  });

  // Edit profile form state
  const [name, setName] = useState(user?.name || '');
  const [college, setCollege] = useState(user?.college || '');
  const [gradYear, setGradYear] = useState(user?.grad_year || 2026);
  const [targetRole, setTargetRole] = useState(user?.target_role || 'Software Engineer');
  const [targetCompanies, setTargetCompanies] = useState(
    (user?.target_companies || ['Google', 'Microsoft', 'Amazon']).join(', ')
  );

  // Password change state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState(null);

  // Delete modal state
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteConfirmationText, setDeleteConfirmationText] = useState('');

  // Update profile mutation
  const updateProfileMutation = useMutation({
    mutationFn: () =>
      updateUserProfile({
        name: name.trim(),
        college: college.trim() || null,
        grad_year: gradYear ? Number(gradYear) : null,
        target_role: targetRole.trim() || null,
        target_companies: targetCompanies
          .split(',')
          .map((c) => c.trim())
          .filter(Boolean),
      }),
    onSuccess: (updated) => {
      setUser(updated);
      refetch();
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
      toast.success('Profile details successfully updated');
    },
    onError: (err) => {
      toast.error(err?.message || 'Failed to update profile');
    },
  });

  // Change password mutation
  const changePasswordMutation = useMutation({
    mutationFn: () => {
      if (newPassword.length < 10) {
        throw new Error('New password must be at least 10 characters long');
      }
      if (newPassword !== confirmPassword) {
        throw new Error('New passwords do not match');
      }
      return changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
    },
    onSuccess: () => {
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setPasswordError(null);
      toast.success('Password changed successfully');
    },
    onError: (err) => {
      setPasswordError(err?.message || 'Password change failed');
      toast.error(err?.message || 'Password update failed');
    },
  });

  // Export data handler
  const handleExportData = async () => {
    try {
      const data = await exportUserData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `placement-copilot-export-${new Date().toISOString().slice(0, 10)}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      toast.success('Data exported as JSON');
    } catch {
      toast.error('Failed to export candidate data');
    }
  };

  // Delete account mutation
  const deleteAccountMutation = useMutation({
    mutationFn: () => deleteAccount(),
    onSuccess: async () => {
      toast.success('Account permanently deleted');
      await logout();
      navigate('/login');
    },
    onError: (err) => {
      toast.error(err?.message || 'Failed to delete account');
    },
  });

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="border-b border-[#1f1f1f] pb-5">
        <div className="label-mono text-xs text-[#4be277] mb-1">CANDIDATE ACCOUNT & SECURITY</div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-[#e2e2e2] tracking-tight">
          Candidate Profile & Settings
        </h1>
        <p className="text-xs text-[#869585] mt-0.5">
          Manage your placement targets, academic background, security credentials, and data privacy.
        </p>
      </div>

      {/* Profile Card */}
      <div className="p-6 rounded-[8px] bg-[#1b1b1b] border border-[#2a2a2a] space-y-5">
        <div className="flex items-center justify-between pb-3 border-b border-[#2a2a2a]">
          <div className="flex items-center gap-2">
            <Icon name="person" className="text-sm text-[#4be277]" />
            <h3 className="font-bold text-sm text-[#e2e2e2]">Placement Preparation Profile</h3>
          </div>
          <span className="label-mono text-[10px] text-[#869585]">AUTHENTICATED IDENTITY</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block label-mono text-[10px] text-[#869585] mb-1">FULL NAME</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 rounded-[2px] bg-[#131313] border border-[#3d4a3d] text-xs text-[#e2e2e2] focus:border-[#4be277]"
            />
          </div>

          <div>
            <label className="block label-mono text-[10px] text-[#869585] mb-1">EMAIL ADDRESS (PRIMARY)</label>
            <input
              type="email"
              disabled
              value={user?.email || ''}
              className="w-full px-3 py-2 rounded-[2px] bg-[#131313] border border-[#2a2a2a] text-xs text-[#869585] cursor-not-allowed opacity-75"
            />
          </div>

          <div>
            <label className="block label-mono text-[10px] text-[#869585] mb-1">COLLEGE / UNIVERSITY</label>
            <input
              type="text"
              value={college}
              onChange={(e) => setCollege(e.target.value)}
              placeholder="e.g. Stanford University / IIT Bombay"
              className="w-full px-3 py-2 rounded-[2px] bg-[#131313] border border-[#3d4a3d] text-xs text-[#e2e2e2] focus:border-[#4be277]"
            />
          </div>

          <div>
            <label className="block label-mono text-[10px] text-[#869585] mb-1">GRADUATION YEAR</label>
            <input
              type="number"
              value={gradYear}
              onChange={(e) => setGradYear(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-[2px] bg-[#131313] border border-[#3d4a3d] text-xs text-[#e2e2e2] focus:border-[#4be277]"
            />
          </div>

          <div>
            <label className="block label-mono text-[10px] text-[#869585] mb-1">TARGET ROLE</label>
            <input
              type="text"
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
              placeholder="e.g. Software Engineer / SDE 1"
              className="w-full px-3 py-2 rounded-[2px] bg-[#131313] border border-[#3d4a3d] text-xs text-[#e2e2e2] focus:border-[#4be277]"
            />
          </div>

          <div>
            <label className="block label-mono text-[10px] text-[#869585] mb-1">
              TARGET COMPANIES (COMMA SEPARATED)
            </label>
            <input
              type="text"
              value={targetCompanies}
              onChange={(e) => setTargetCompanies(e.target.value)}
              placeholder="Google, Microsoft, Amazon, Stripe"
              className="w-full px-3 py-2 rounded-[2px] bg-[#131313] border border-[#3d4a3d] text-xs text-[#e2e2e2] focus:border-[#4be277]"
            />
          </div>
        </div>

        <div className="pt-2 flex justify-end">
          <button
            onClick={() => updateProfileMutation.mutate()}
            disabled={updateProfileMutation.isPending}
            className="px-5 py-2 rounded-[4px] bg-[#4be277] text-[#003915] text-xs font-bold uppercase tracking-wider hover:bg-[#22c55e] transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            {updateProfileMutation.isPending && (
              <div className="w-3.5 h-3.5 border-2 border-[#003915] border-t-transparent rounded-full animate-spin" />
            )}
            <span>Save Profile Changes</span>
          </button>
        </div>
      </div>

      {/* Security & Password Change */}
      <div className="p-6 rounded-[8px] bg-[#1b1b1b] border border-[#2a2a2a] space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#2a2a2a]">
          <div className="flex items-center gap-2">
            <Icon name="lock" className="text-sm text-[#4be277]" />
            <h3 className="font-bold text-sm text-[#e2e2e2]">Change Password</h3>
          </div>
          <span className="label-mono text-[10px] text-[#869585]">ARGON2ID HASHED</span>
        </div>

        {passwordError && (
          <div className="p-3 rounded-[4px] bg-[#93000a]/20 border border-[#ffb4ab]/40 text-xs text-[#ffb4ab]">
            {passwordError}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="block label-mono text-[10px] text-[#869585] mb-1">CURRENT PASSWORD</label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="w-full px-3 py-2 rounded-[2px] bg-[#131313] border border-[#3d4a3d] text-xs text-[#e2e2e2] focus:border-[#4be277]"
            />
          </div>
          <div>
            <label className="block label-mono text-[10px] text-[#869585] mb-1">NEW PASSWORD (MIN 10)</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full px-3 py-2 rounded-[2px] bg-[#131313] border border-[#3d4a3d] text-xs text-[#e2e2e2] focus:border-[#4be277]"
            />
          </div>
          <div>
            <label className="block label-mono text-[10px] text-[#869585] mb-1">CONFIRM NEW PASSWORD</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full px-3 py-2 rounded-[2px] bg-[#131313] border border-[#3d4a3d] text-xs text-[#e2e2e2] focus:border-[#4be277]"
            />
          </div>
        </div>

        <div className="pt-2 flex justify-end">
          <button
            onClick={() => changePasswordMutation.mutate()}
            disabled={changePasswordMutation.isPending || !currentPassword || !newPassword}
            className="px-4 py-2 rounded-[4px] bg-[#1f1f1f] border border-[#3d4a3d] text-xs text-[#e2e2e2] font-semibold hover:border-[#4be277] transition-colors disabled:opacity-50"
          >
            Update Password
          </button>
        </div>
      </div>

      {/* Data Management & GDPR/Account Privacy */}
      <div className="p-6 rounded-[8px] bg-[#1b1b1b] border border-[#2a2a2a] space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#2a2a2a]">
          <div className="flex items-center gap-2">
            <Icon name="shield" className="text-sm text-[#4be277]" />
            <h3 className="font-bold text-sm text-[#e2e2e2]">Data Export & Account Termination</h3>
          </div>
          <span className="label-mono text-[10px] text-[#869585]">DATA INTEGRITY</span>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-[4px] bg-[#1f1f1f] border border-[#2a2a2a]">
          <div>
            <div className="text-xs font-bold text-[#e2e2e2]">Export Full Account Data (JSON)</div>
            <div className="text-[11px] text-[#869585] mt-0.5">
              Download your complete practice attempts, resume parsed data, mock interviews, and snapshots.
            </div>
          </div>
          <button
            onClick={handleExportData}
            className="px-4 py-2 rounded-[4px] bg-[#131313] border border-[#3d4a3d] text-xs text-[#4be277] font-semibold hover:bg-[#4be277]/10 flex items-center gap-1.5 self-start sm:self-auto shrink-0"
          >
            <Icon name="download" className="text-sm" />
            <span>Export Data</span>
          </button>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-[4px] bg-[#93000a]/10 border border-[#ffb4ab]/30">
          <div>
            <div className="text-xs font-bold text-[#ffb4ab]">Permanently Delete Account</div>
            <div className="text-[11px] text-[#869585] mt-0.5">
              Permanently purges all user data, attempts, resumes, and interview records with cascading deletion.
            </div>
          </div>
          <button
            onClick={() => setShowDeleteModal(true)}
            className="px-4 py-2 rounded-[4px] bg-[#93000a] text-[#ffb4ab] text-xs font-bold uppercase tracking-wider hover:bg-[#93000a]/80 self-start sm:self-auto shrink-0"
          >
            Delete Account
          </button>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-xs">
          <div className="bg-[#1f1f1f] border border-[#ffb4ab]/40 rounded-[8px] max-w-md w-full p-6 space-y-4">
            <div className="flex items-center gap-2 text-[#ffb4ab]">
              <Icon name="warning" className="text-2xl" />
              <h3 className="text-base font-bold">Irreversible Action Warning</h3>
            </div>
            <p className="text-xs text-[#bccbb9] leading-relaxed">
              This action will immediately and irreversibly delete your candidate profile, all tracked DSA attempts, resumes, and mock interview transcripts.
            </p>
            <div>
              <label className="block text-[11px] text-[#869585] mb-1">
                Type <strong className="text-[#ffb4ab]">DELETE</strong> to confirm:
              </label>
              <input
                type="text"
                value={deleteConfirmationText}
                onChange={(e) => setDeleteConfirmationText(e.target.value)}
                placeholder="DELETE"
                className="w-full px-3 py-2 rounded-[2px] bg-[#131313] border border-[#3d4a3d] text-xs text-[#e2e2e2] focus:border-[#ffb4ab]"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setDeleteConfirmationText('');
                }}
                className="px-4 py-1.5 rounded-[4px] bg-[#131313] text-xs text-[#869585]"
              >
                Cancel
              </button>
              <button
                onClick={() => deleteAccountMutation.mutate()}
                disabled={deleteConfirmationText !== 'DELETE' || deleteAccountMutation.isPending}
                className="px-4 py-1.5 rounded-[4px] bg-[#93000a] text-[#ffb4ab] text-xs font-bold uppercase tracking-wider hover:bg-[#93000a]/80 disabled:opacity-40"
              >
                Permanently Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProfilePage;
