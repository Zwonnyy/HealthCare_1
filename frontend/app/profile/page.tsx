"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import Navbar from "@/components/Navbar";
import { userApi, UserInfo } from "@/lib/api";
import { getToken, saveUser } from "@/lib/auth";

export default function ProfilePage() {
  const router = useRouter();
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploadingImage, setUploadingImage] = useState(false);

  const [form, setForm] = useState({
    name: "",
    email: "",
    phone_number: "",
    birthday: "",
    gender: "" as "MALE" | "FEMALE" | "",
  });

  const [pwForm, setPwForm] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [changingPw, setChangingPw] = useState(false);

  useEffect(() => {
    if (!getToken()) { router.replace("/login"); return; }
    userApi.me()
      .then(({ data }) => {
        setUserInfo(data);
        setForm({
          name: data.name,
          email: data.email,
          phone_number: data.phone_number,
          birthday: data.birthday,
          gender: data.gender,
        });
      })
      .catch(() => toast.error("프로필을 불러오지 못했어요."))
      .finally(() => setLoading(false));
  }, [router]);

  async function handleSaveProfile() {
    setSaving(true);
    try {
      const updated = await userApi.updateMe({
        name: form.name,
        email: form.email,
        phone_number: form.phone_number,
        birthday: form.birthday,
        gender: form.gender as "MALE" | "FEMALE",
      });
      setUserInfo(updated.data);
      saveUser(updated.data);
      toast.success("프로필을 수정했어요.");
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(msg ?? "수정에 실패했어요.");
    } finally {
      setSaving(false);
    }
  }

  async function handleProfileImageChange(file: File | undefined) {
    if (!file) return;
    setUploadingImage(true);
    try {
      const updated = await userApi.uploadProfileImage(file);
      setUserInfo(updated.data);
      saveUser(updated.data);
      toast.success("프로필 이미지를 변경했어요.");
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(msg ?? "이미지 업로드에 실패했어요.");
    } finally {
      setUploadingImage(false);
    }
  }

  async function handleChangePw() {
    if (pwForm.new_password !== pwForm.confirm_password) {
      toast.error("새 비밀번호가 일치하지 않아요.");
      return;
    }
    if (pwForm.new_password.length < 8) {
      toast.error("새 비밀번호는 8자 이상이어야 해요.");
      return;
    }
    setChangingPw(true);
    try {
      await userApi.updateMe({
        current_password: pwForm.current_password,
        new_password: pwForm.new_password,
      });
      setPwForm({ current_password: "", new_password: "", confirm_password: "" });
      toast.success("비밀번호를 변경했어요.");
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(msg ?? "비밀번호 변경에 실패했어요.");
    } finally {
      setChangingPw(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-50 dark:bg-zinc-900">
        <Navbar />
        <div className="max-w-2xl mx-auto px-4 py-16 space-y-4">
          {[1, 2, 3].map((i) => <div key={i} className="h-16 rounded-xl bg-zinc-200 dark:bg-zinc-800 animate-pulse" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-900">
      <Navbar />
      <main className="max-w-2xl mx-auto px-4 py-10 space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">프로필</h1>
          <p className="text-sm text-zinc-500 mt-1">내 정보를 수정하고 비밀번호를 변경할 수 있어요.</p>
        </div>

        <div className="bg-white dark:bg-zinc-800 rounded-2xl border border-zinc-100 dark:border-zinc-700 shadow-sm p-6">
          <div className="flex items-center gap-4 mb-6 pb-6 border-b border-zinc-100 dark:border-zinc-700">
            {userInfo?.profile_image_url ? (
              <img
                src={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}${userInfo.profile_image_url}`}
                alt={`${userInfo.name} 프로필`}
                className="w-16 h-16 rounded-full object-cover border border-zinc-200 dark:border-zinc-700"
              />
            ) : (
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center text-white text-2xl font-bold">
                {userInfo?.role === "DOCTOR" ? "의" : "환"}
              </div>
            )}
            <div>
              <p className="font-semibold text-zinc-900 dark:text-zinc-100 text-lg">{userInfo?.name}</p>
              <p className="text-sm text-zinc-500">{userInfo?.role === "DOCTOR" ? "🩺 의사" : "🧑 환자"}</p>
              <p className="text-xs text-zinc-400 mt-0.5">{userInfo?.email}</p>
              <label className="mt-3 inline-flex cursor-pointer items-center rounded-md border border-zinc-200 dark:border-zinc-600 px-3 py-1.5 text-xs font-medium text-zinc-600 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-700">
                {uploadingImage ? "업로드 중..." : "프로필 이미지 변경"}
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  className="hidden"
                  disabled={uploadingImage}
                  onChange={(e) => handleProfileImageChange(e.target.files?.[0])}
                />
              </label>
            </div>
          </div>

          <h2 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300 mb-4">기본 정보 수정</h2>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="mb-1.5">이름</Label>
                <Input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="dark:bg-zinc-700 dark:border-zinc-600"
                />
              </div>
              <div>
                <Label className="mb-1.5">이메일</Label>
                <Input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  className="dark:bg-zinc-700 dark:border-zinc-600"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="mb-1.5">전화번호</Label>
                <Input
                  value={form.phone_number}
                  onChange={(e) => setForm({ ...form, phone_number: e.target.value })}
                  placeholder="010-0000-0000"
                  className="dark:bg-zinc-700 dark:border-zinc-600"
                />
              </div>
              <div>
                <Label className="mb-1.5">생년월일</Label>
                <Input
                  type="date"
                  value={form.birthday}
                  onChange={(e) => setForm({ ...form, birthday: e.target.value })}
                  className="dark:bg-zinc-700 dark:border-zinc-600"
                />
              </div>
            </div>
            <div>
              <Label className="mb-1.5">성별</Label>
              <div className="flex gap-3">
                {(["MALE", "FEMALE"] as const).map((g) => (
                  <button
                    key={g}
                    onClick={() => setForm({ ...form, gender: g })}
                    className={`flex-1 py-2 rounded-lg text-sm border transition-colors ${
                      form.gender === g
                        ? "border-blue-500 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400"
                        : "border-zinc-200 dark:border-zinc-600 text-zinc-600 dark:text-zinc-400 hover:border-zinc-300"
                    }`}
                  >
                    {g === "MALE" ? "남성" : "여성"}
                  </button>
                ))}
              </div>
            </div>
          </div>
          <Button
            className="mt-6 bg-blue-700 hover:bg-blue-800 w-full"
            onClick={handleSaveProfile}
            disabled={saving}
          >
            {saving ? "저장 중…" : "정보 저장"}
          </Button>
        </div>

        <div className="bg-white dark:bg-zinc-800 rounded-2xl border border-zinc-100 dark:border-zinc-700 shadow-sm p-6">
          <h2 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300 mb-4">비밀번호 변경</h2>
          <div className="space-y-4">
            <div>
              <Label className="mb-1.5">현재 비밀번호</Label>
              <Input
                type="password"
                value={pwForm.current_password}
                onChange={(e) => setPwForm({ ...pwForm, current_password: e.target.value })}
                className="dark:bg-zinc-700 dark:border-zinc-600"
              />
            </div>
            <div>
              <Label className="mb-1.5">새 비밀번호</Label>
              <Input
                type="password"
                value={pwForm.new_password}
                onChange={(e) => setPwForm({ ...pwForm, new_password: e.target.value })}
                placeholder="8자 이상"
                className="dark:bg-zinc-700 dark:border-zinc-600"
              />
            </div>
            <div>
              <Label className="mb-1.5">새 비밀번호 확인</Label>
              <Input
                type="password"
                value={pwForm.confirm_password}
                onChange={(e) => setPwForm({ ...pwForm, confirm_password: e.target.value })}
                className="dark:bg-zinc-700 dark:border-zinc-600"
              />
            </div>
          </div>
          <Button
            className="mt-6 bg-blue-700 hover:bg-blue-800 w-full"
            onClick={handleChangePw}
            disabled={changingPw || !pwForm.current_password || !pwForm.new_password}
          >
            {changingPw ? "변경 중…" : "비밀번호 변경"}
          </Button>
        </div>
      </main>
    </div>
  );
}
