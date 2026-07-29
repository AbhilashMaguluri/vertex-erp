import React, { useState } from 'react';
import {
  Save,
  CheckCircle2,
  Sliders,
  Users,
  ShieldAlert,
  History,
  Plus,
  Trash2,
  AlertCircle,
} from 'lucide-react';
import {
  useAdminCounsellors,
  useUpdateAdminCounsellor,
  useCampusEmergencyContacts,
  useAdminCreateEmergencyContact,
  useAdminDeleteEmergencyContact,
  useAdminAuditLogs,
} from '../api/reachOutApi';
import { CounsellorContactProfile } from '../types/reachOut';

export function AdminReachOutConfigView() {
  const [activeTab, setActiveTab] = useState<'PROFILES' | 'EMERGENCY' | 'AUDIT'>('PROFILES');

  const { data: counsellors, isLoading: isCounsellorsLoading } = useAdminCounsellors();
  const { data: emergencyContacts, isLoading: isEmergencyLoading } = useCampusEmergencyContacts();
  const { data: auditLogs, isLoading: isAuditLoading } = useAdminAuditLogs();

  const [selectedCounsellor, setSelectedCounsellor] = useState<CounsellorContactProfile | null>(null);

  const updateCounsellorMutation = useUpdateAdminCounsellor();
  const createEmergencyMutation = useAdminCreateEmergencyContact();
  const deleteEmergencyMutation = useAdminDeleteEmergencyContact();

  const [formError, setFormError] = useState<string | null>(null);

  // Profile form state (all 22 attributes)
  const [photoUrl, setPhotoUrl] = useState('');
  const [designation, setDesignation] = useState('');
  const [departmentName, setDepartmentName] = useState('');
  const [yearsExperience, setYearsExperience] = useState<number>(5);
  const [specializationsText, setSpecializationsText] = useState('');
  const [languagesText, setLanguagesText] = useState('');
  const [aboutMe, setAboutMe] = useState('');
  const [researchInterests, setResearchInterests] = useState('');

  const [building, setBuilding] = useState('');
  const [floor, setFloor] = useState('');
  const [cabinNumber, setCabinNumber] = useState('');
  const [officePhone, setOfficePhone] = useState('');
  const [emergencyPhone, setEmergencyPhone] = useState('');
  const [mapsUrl, setMapsUrl] = useState('');
  const [officeStatus, setOfficeStatus] = useState<'AVAILABLE' | 'BUSY' | 'IN_SESSION' | 'ON_LEAVE' | 'OFFLINE'>('AVAILABLE');
  const [statusMessage, setStatusMessage] = useState('');

  const [whatsappNumber, setWhatsappNumber] = useState('');
  const [linkedinUrl, setLinkedinUrl] = useState('');
  const [teamsUrl, setTeamsUrl] = useState('');
  const [googleMeetUrl, setGoogleMeetUrl] = useState('');
  const [zoomUrl, setZoomUrl] = useState('');
  const [telegramUrl, setTelegramUrl] = useState('');
  const [collegeEmail, setCollegeEmail] = useState('');

  // Emergency contact modal/form state
  const [showAddEmergency, setShowAddEmergency] = useState(false);
  const [emName, setEmName] = useState('');
  const [emCategory, setEmCategory] = useState('GENERAL');
  const [emPhone, setEmPhone] = useState('');
  const [emEmail, setEmEmail] = useState('');
  const [emLocation, setEmLocation] = useState('');

  React.useEffect(() => {
    if (counsellors && counsellors.length > 0 && !selectedCounsellor) {
      handleSelectCounsellor(counsellors[0]);
    }
  }, [counsellors]);

  const handleSelectCounsellor = (c: CounsellorContactProfile) => {
    setSelectedCounsellor(c);
    setFormError(null);

    setPhotoUrl(c.photo_url || '');
    setDesignation(c.designation || 'Student Counsellor');
    setDepartmentName(c.department_name || '');
    setYearsExperience(c.years_experience || 0);
    setSpecializationsText((c.specializations || []).join(', '));
    setLanguagesText((c.languages_spoken || []).join(', '));
    setAboutMe(c.about_me || '');
    setResearchInterests(c.research_interests || '');

    setBuilding(c.building || '');
    setFloor(c.floor || '');
    setCabinNumber(c.cabin_number || '');
    setOfficePhone(c.office_phone || '');
    setEmergencyPhone(c.emergency_alternate_phone || '');
    setMapsUrl(c.maps_url || '');
    setOfficeStatus(c.office_status || 'AVAILABLE');
    setStatusMessage(c.status_message || '');

    setWhatsappNumber(c.whatsapp_number || '');
    setLinkedinUrl(c.linkedin_url || '');
    setTeamsUrl(c.teams_url || '');
    setGoogleMeetUrl(c.google_meet_url || '');
    setZoomUrl(c.zoom_url || '');
    setTelegramUrl(c.telegram_url || '');
    setCollegeEmail(c.college_email || '');
  };

  const handleSaveProfile = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCounsellor) return;
    setFormError(null);

    const specializations = specializationsText.split(',').map((s) => s.trim()).filter(Boolean);
    const languages_spoken = languagesText.split(',').map((s) => s.trim()).filter(Boolean);

    updateCounsellorMutation.mutate(
      {
        counsellorId: selectedCounsellor.counsellor_id,
        data: {
          photo_url: photoUrl || null,
          designation,
          department_name: departmentName,
          years_experience: Number(yearsExperience),
          specializations,
          languages_spoken,
          about_me: aboutMe || null,
          research_interests: researchInterests || null,
          building,
          floor,
          cabin_number: cabinNumber,
          office_phone: officePhone || null,
          emergency_alternate_phone: emergencyPhone || null,
          maps_url: mapsUrl || null,
          office_status: officeStatus,
          status_message: statusMessage || null,
          whatsapp_number: whatsappNumber || null,
          linkedin_url: linkedinUrl || null,
          teams_url: teamsUrl || null,
          google_meet_url: googleMeetUrl || null,
          zoom_url: zoomUrl || null,
          telegram_url: telegramUrl || null,
          college_email: collegeEmail || null,
        },
      },
      {
        onError: (err: any) => {
          const detail = err.response?.data?.detail;
          if (Array.isArray(detail)) {
            setFormError(detail.map((d: any) => `${d.loc?.join('.')}: ${d.msg}`).join(' | '));
          } else {
            setFormError(detail || 'Failed to update counsellor profile.');
          }
        },
      }
    );
  };

  const handleAddEmergencyContact = (e: React.FormEvent) => {
    e.preventDefault();
    createEmergencyMutation.mutate(
      {
        name: emName,
        category: emCategory,
        phone: emPhone,
        email: emEmail || undefined,
        location: emLocation || undefined,
        is_24_7: true,
        display_order: (emergencyContacts?.length || 0) + 1,
      },
      {
        onSuccess: () => {
          setShowAddEmergency(false);
          setEmName('');
          setEmPhone('');
          setEmEmail('');
          setEmLocation('');
        },
      }
    );
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="rounded-3xl border border-border/80 bg-card p-6 shadow-xl relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-600/10 text-brand-600 ring-4 ring-brand-600/10">
              <Sliders className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-xl font-black text-foreground">Reach Out Administrator Desk</h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                Manage counsellor profiles, emergency hotlines, and view system audit configuration logs.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('PROFILES')}
              className={`px-4 py-2 text-xs font-bold rounded-xl transition-all ${
                activeTab === 'PROFILES' ? 'bg-brand-600 text-white shadow-md' : 'bg-muted text-muted-foreground hover:bg-accent'
              }`}
            >
              Counsellor Profiles
            </button>
            <button
              onClick={() => setActiveTab('EMERGENCY')}
              className={`px-4 py-2 text-xs font-bold rounded-xl transition-all ${
                activeTab === 'EMERGENCY' ? 'bg-brand-600 text-white shadow-md' : 'bg-muted text-muted-foreground hover:bg-accent'
              }`}
            >
              Emergency Contacts
            </button>
            <button
              onClick={() => setActiveTab('AUDIT')}
              className={`px-4 py-2 text-xs font-bold rounded-xl transition-all ${
                activeTab === 'AUDIT' ? 'bg-brand-600 text-white shadow-md' : 'bg-muted text-muted-foreground hover:bg-accent'
              }`}
            >
              Audit Logs History
            </button>
          </div>
        </div>
      </div>

      {/* TAB 1: COUNSELLOR PROFILES EDITOR */}
      {activeTab === 'PROFILES' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Counsellor Selector List */}
          <div className="rounded-3xl border border-border/80 bg-card p-5 shadow-xl space-y-3">
            <h3 className="text-xs font-black uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <Users className="h-4 w-4 text-brand-600" /> Select Counsellor
            </h3>

            {isCounsellorsLoading ? (
              <div className="py-8 text-center text-xs font-bold text-muted-foreground">Loading counsellors...</div>
            ) : (
              <div className="space-y-2">
                {counsellors?.map((c) => (
                  <div
                    key={c.id}
                    onClick={() => handleSelectCounsellor(c)}
                    className={`p-3 rounded-2xl border transition-all cursor-pointer flex items-center justify-between ${
                      selectedCounsellor?.id === c.id
                        ? 'bg-brand-600/10 border-brand-600 shadow-sm'
                        : 'bg-muted/30 border-border/50 hover:bg-accent'
                    }`}
                  >
                    <div className="flex items-center gap-3 truncate">
                      <div className="h-9 w-9 rounded-xl bg-brand-600/10 text-brand-600 font-extrabold flex items-center justify-center shrink-0 overflow-hidden">
                        {c.photo_url ? <img src={c.photo_url} alt="" className="h-full w-full object-cover" /> : c.full_name.charAt(0)}
                      </div>
                      <div className="truncate">
                        <span className="text-xs font-black text-foreground block truncate">{c.full_name}</span>
                        <span className="text-[10px] text-muted-foreground font-semibold block truncate">
                          {c.department_name}
                        </span>
                      </div>
                    </div>
                    <span className="text-[10px] font-black uppercase text-emerald-600 bg-emerald-500/10 px-2 py-0.5 rounded-full">
                      {c.office_status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Right: Full Profile Editor Form */}
          <div className="lg:col-span-2 rounded-3xl border border-border/80 bg-card p-6 shadow-xl space-y-4">
            {selectedCounsellor ? (
              <form onSubmit={handleSaveProfile} className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-border/60">
                  <h3 className="text-base font-black text-foreground">
                    Configuring Profile: {selectedCounsellor.full_name}
                  </h3>
                  <span className="text-xs font-bold text-brand-600 bg-brand-500/10 px-3 py-1 rounded-full">
                    ID: {selectedCounsellor.counsellor_id.substring(0, 8)}
                  </span>
                </div>

                {formError && (
                  <div className="p-3 rounded-xl bg-rose-500/10 text-rose-600 text-xs font-semibold flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 shrink-0" /> {formError}
                  </div>
                )}

                {/* Section 1: Basic Info */}
                <div className="space-y-3">
                  <h4 className="text-xs font-black uppercase text-muted-foreground tracking-wider">
                    Basic Profile Attributes
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div>
                      <label className="text-xs font-bold text-foreground block mb-1">Designation</label>
                      <input
                        type="text"
                        value={designation}
                        onChange={(e) => setDesignation(e.target.value)}
                        required
                        className="w-full rounded-xl bg-muted/40 p-2.5 text-xs font-bold border border-border/60"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-bold text-foreground block mb-1">Department</label>
                      <input
                        type="text"
                        value={departmentName}
                        onChange={(e) => setDepartmentName(e.target.value)}
                        required
                        className="w-full rounded-xl bg-muted/40 p-2.5 text-xs font-bold border border-border/60"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-bold text-foreground block mb-1">Years Experience</label>
                      <input
                        type="number"
                        value={yearsExperience}
                        onChange={(e) => setYearsExperience(Number(e.target.value))}
                        required
                        className="w-full rounded-xl bg-muted/40 p-2.5 text-xs font-bold border border-border/60"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs font-bold text-foreground block mb-1">Photo Image URL</label>
                      <input
                        type="text"
                        value={photoUrl}
                        onChange={(e) => setPhotoUrl(e.target.value)}
                        placeholder="https://..."
                        className="w-full rounded-xl bg-muted/40 p-2.5 text-xs font-bold border border-border/60"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-bold text-foreground block mb-1">College Email</label>
                      <input
                        type="email"
                        value={collegeEmail}
                        onChange={(e) => setCollegeEmail(e.target.value)}
                        className="w-full rounded-xl bg-muted/40 p-2.5 text-xs font-bold border border-border/60"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs font-bold text-foreground block mb-1">Specializations (Comma separated)</label>
                      <input
                        type="text"
                        value={specializationsText}
                        onChange={(e) => setSpecializationsText(e.target.value)}
                        placeholder="Academic Counselling, Career Guidance..."
                        className="w-full rounded-xl bg-muted/40 p-2.5 text-xs font-bold border border-border/60"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-bold text-foreground block mb-1">Languages Spoken (Comma separated)</label>
                      <input
                        type="text"
                        value={languagesText}
                        onChange={(e) => setLanguagesText(e.target.value)}
                        placeholder="English, Telugu, Hindi..."
                        className="w-full rounded-xl bg-muted/40 p-2.5 text-xs font-bold border border-border/60"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-xs font-bold text-foreground block mb-1">Professional Bio / About Me</label>
                    <textarea
                      value={aboutMe}
                      onChange={(e) => setAboutMe(e.target.value)}
                      rows={2}
                      className="w-full rounded-xl bg-muted/40 p-2.5 text-xs font-medium border border-border/60 resize-none"
                    />
                  </div>
                </div>

                {/* Section 2: Cabin & Location */}
                <div className="space-y-3 pt-3 border-t border-border/60">
                  <h4 className="text-xs font-black uppercase text-muted-foreground tracking-wider">
                    Cabin & Google Maps Location
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div>
                      <label className="text-xs font-bold text-foreground block mb-1">Building</label>
                      <input
                        type="text"
                        value={building}
                        onChange={(e) => setBuilding(e.target.value)}
                        required
                        className="w-full rounded-xl bg-muted/40 p-2.5 text-xs font-bold border border-border/60"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-bold text-foreground block mb-1">Floor</label>
                      <input
                        type="text"
                        value={floor}
                        onChange={(e) => setFloor(e.target.value)}
                        required
                        className="w-full rounded-xl bg-muted/40 p-2.5 text-xs font-bold border border-border/60"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-bold text-foreground block mb-1">Cabin Room</label>
                      <input
                        type="text"
                        value={cabinNumber}
                        onChange={(e) => setCabinNumber(e.target.value)}
                        required
                        className="w-full rounded-xl bg-muted/40 p-2.5 text-xs font-bold border border-border/60"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div>
                      <label className="text-xs font-bold text-foreground block mb-1">Office Hotline Phone</label>
                      <input
                        type="text"
                        value={officePhone}
                        onChange={(e) => setOfficePhone(e.target.value)}
                        placeholder="+91..."
                        className="w-full rounded-xl bg-muted/40 p-2.5 text-xs font-bold border border-border/60"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-bold text-foreground block mb-1">Emergency Alternate Phone</label>
                      <input
                        type="text"
                        value={emergencyPhone}
                        onChange={(e) => setEmergencyPhone(e.target.value)}
                        placeholder="+91..."
                        className="w-full rounded-xl bg-muted/40 p-2.5 text-xs font-bold border border-border/60"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-bold text-foreground block mb-1">Google Maps URL</label>
                      <input
                        type="text"
                        value={mapsUrl}
                        onChange={(e) => setMapsUrl(e.target.value)}
                        placeholder="https://maps.google.com/?q=..."
                        className="w-full rounded-xl bg-muted/40 p-2.5 text-xs font-bold border border-border/60"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs font-bold text-foreground block mb-1">Office Status</label>
                      <select
                        value={officeStatus}
                        onChange={(e) => setOfficeStatus(e.target.value as any)}
                        className="w-full rounded-xl bg-muted/40 p-2.5 text-xs font-bold border border-border/60"
                      >
                        <option value="AVAILABLE">Available</option>
                        <option value="BUSY">Busy</option>
                        <option value="IN_SESSION">In Session</option>
                        <option value="ON_LEAVE">On Leave</option>
                        <option value="OFFLINE">Offline</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-xs font-bold text-foreground block mb-1">Status Message</label>
                      <input
                        type="text"
                        value={statusMessage}
                        onChange={(e) => setStatusMessage(e.target.value)}
                        placeholder="Available for student counselling..."
                        className="w-full rounded-xl bg-muted/40 p-2.5 text-xs font-bold border border-border/60"
                      />
                    </div>
                  </div>
                </div>

                {/* Section 3: Channel Links */}
                <div className="space-y-3 pt-3 border-t border-border/60">
                  <h4 className="text-xs font-black uppercase text-muted-foreground tracking-wider">
                    Direct Communication Channel Links
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div>
                      <label className="text-xs font-bold text-foreground block mb-1">WhatsApp Number</label>
                      <input
                        type="text"
                        value={whatsappNumber}
                        onChange={(e) => setWhatsappNumber(e.target.value)}
                        placeholder="+91..."
                        className="w-full rounded-xl bg-muted/40 p-2.5 text-xs font-bold border border-border/60"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-bold text-foreground block mb-1">MS Teams URL</label>
                      <input
                        type="text"
                        value={teamsUrl}
                        onChange={(e) => setTeamsUrl(e.target.value)}
                        placeholder="https://teams.microsoft.com/..."
                        className="w-full rounded-xl bg-muted/40 p-2.5 text-xs font-bold border border-border/60"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-bold text-foreground block mb-1">Google Meet URL</label>
                      <input
                        type="text"
                        value={googleMeetUrl}
                        onChange={(e) => setGoogleMeetUrl(e.target.value)}
                        placeholder="https://meet.google.com/..."
                        className="w-full rounded-xl bg-muted/40 p-2.5 text-xs font-bold border border-border/60"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-bold text-foreground block mb-1">Zoom Meeting Link</label>
                      <input
                        type="text"
                        value={zoomUrl}
                        onChange={(e) => setZoomUrl(e.target.value)}
                        placeholder="https://zoom.us/j/..."
                        className="w-full rounded-xl bg-muted/40 p-2.5 text-xs font-bold border border-border/60"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-bold text-foreground block mb-1">LinkedIn Profile</label>
                      <input
                        type="text"
                        value={linkedinUrl}
                        onChange={(e) => setLinkedinUrl(e.target.value)}
                        placeholder="https://linkedin.com/in/..."
                        className="w-full rounded-xl bg-muted/40 p-2.5 text-xs font-bold border border-border/60"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-bold text-foreground block mb-1">Telegram Link</label>
                      <input
                        type="text"
                        value={telegramUrl}
                        onChange={(e) => setTelegramUrl(e.target.value)}
                        placeholder="https://t.me/..."
                        className="w-full rounded-xl bg-muted/40 p-2.5 text-xs font-bold border border-border/60"
                      />
                    </div>
                  </div>
                </div>

                {updateCounsellorMutation.isSuccess && (
                  <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-600 text-xs font-bold flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4" /> Counsellor profile configuration saved and audit log generated!
                  </div>
                )}

                <div className="pt-2 flex justify-end">
                  <button
                    type="submit"
                    disabled={updateCounsellorMutation.isPending}
                    className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-6 py-2.5 text-xs font-bold text-white shadow-md hover:bg-brand-700 transition-all cursor-pointer"
                  >
                    <Save className="h-4 w-4" />
                    {updateCounsellorMutation.isPending ? 'Saving Config...' : 'Save Counsellor Config'}
                  </button>
                </div>
              </form>
            ) : (
              <div className="py-12 text-center text-xs font-bold text-muted-foreground">
                Select a counsellor from the left list.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: EMERGENCY CONTACTS MANAGER */}
      {activeTab === 'EMERGENCY' && (
        <div className="rounded-3xl border border-border/80 bg-card p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-black text-foreground flex items-center gap-2">
                <ShieldAlert className="h-5 w-5 text-rose-500" /> Campus Emergency Hotlines Manager
              </h3>
              <p className="text-xs text-muted-foreground mt-0.5">
                Configure official campus safety, medical, anti-ragging, and security emergency contacts.
              </p>
            </div>
            <button
              onClick={() => setShowAddEmergency(!showAddEmergency)}
              className="inline-flex items-center gap-1.5 rounded-xl bg-brand-600 px-4 py-2 text-xs font-bold text-white shadow-md hover:bg-brand-700 cursor-pointer"
            >
              <Plus className="h-4 w-4" /> Add Emergency Hotline
            </button>
          </div>

          {showAddEmergency && (
            <form onSubmit={handleAddEmergencyContact} className="p-4 rounded-2xl bg-muted/40 border border-brand-500/30 space-y-3">
              <h4 className="text-xs font-black text-foreground">Add New Emergency Contact</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div>
                  <label className="text-[10px] font-bold text-muted-foreground block mb-1">Contact Name</label>
                  <input
                    type="text"
                    value={emName}
                    onChange={(e) => setEmName(e.target.value)}
                    required
                    placeholder="e.g. Anti-Ragging Helpline"
                    className="w-full rounded-xl bg-card p-2 text-xs font-bold border border-border/60"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-muted-foreground block mb-1">Category</label>
                  <select
                    value={emCategory}
                    onChange={(e) => setEmCategory(e.target.value)}
                    className="w-full rounded-xl bg-card p-2 text-xs font-bold border border-border/60"
                  >
                    <option value="COUNSELLING">Counselling Office</option>
                    <option value="DEPARTMENT">HOD Office</option>
                    <option value="HEPLINE">Anti Ragging</option>
                    <option value="SAFETY">Women Protection</option>
                    <option value="MEDICAL">Medical Center</option>
                    <option value="SECURITY">Campus Security</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-bold text-muted-foreground block mb-1">Phone Number</label>
                  <input
                    type="text"
                    value={emPhone}
                    onChange={(e) => setEmPhone(e.target.value)}
                    required
                    placeholder="+91..."
                    className="w-full rounded-xl bg-card p-2 text-xs font-bold border border-border/60"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] font-bold text-muted-foreground block mb-1">Email (Optional)</label>
                  <input
                    type="email"
                    value={emEmail}
                    onChange={(e) => setEmEmail(e.target.value)}
                    className="w-full rounded-xl bg-card p-2 text-xs font-bold border border-border/60"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-muted-foreground block mb-1">Location / Room (Optional)</label>
                  <input
                    type="text"
                    value={emLocation}
                    onChange={(e) => setEmLocation(e.target.value)}
                    className="w-full rounded-xl bg-card p-2 text-xs font-bold border border-border/60"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => setShowAddEmergency(false)}
                  className="rounded-xl px-4 py-2 text-xs font-bold text-muted-foreground hover:bg-accent"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createEmergencyMutation.isPending}
                  className="rounded-xl bg-brand-600 px-5 py-2 text-xs font-bold text-white shadow-md hover:bg-brand-700 cursor-pointer"
                >
                  Save Contact
                </button>
              </div>
            </form>
          )}

          {isEmergencyLoading ? (
            <div className="py-8 text-center text-xs font-bold text-muted-foreground">Loading emergency contacts...</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {emergencyContacts?.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between p-3.5 rounded-2xl bg-card border border-border/60 shadow-sm"
                >
                  <div>
                    <span className="text-xs font-black text-foreground block">{item.name}</span>
                    <span className="text-[10px] font-mono text-muted-foreground font-bold">{item.phone}</span>
                    <span className="text-[10px] block text-brand-600 font-bold">{item.location || item.category}</span>
                  </div>

                  <button
                    onClick={() => deleteEmergencyMutation.mutate(item.id)}
                    className="h-8 w-8 rounded-xl bg-rose-500/10 text-rose-600 hover:bg-rose-600 hover:text-white transition-all flex items-center justify-center cursor-pointer"
                    title="Delete contact"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: AUDIT LOGS HISTORY */}
      {activeTab === 'AUDIT' && (
        <div className="rounded-3xl border border-border/80 bg-card p-6 shadow-xl space-y-4">
          <div>
            <h3 className="text-lg font-black text-foreground flex items-center gap-2">
              <History className="h-5 w-5 text-brand-600" /> Admin Reach Out Configuration Audit History
            </h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              Complete database audit trail recording who modified counsellor profiles, channel policies, or emergency hotlines.
            </p>
          </div>

          {isAuditLoading ? (
            <div className="py-8 text-center text-xs font-bold text-muted-foreground">Loading audit log entries...</div>
          ) : (
            <div className="overflow-hidden rounded-2xl border border-border/60">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-muted/40 border-b border-border/60 text-[10px] font-black uppercase text-muted-foreground">
                    <th className="py-3 px-4">Actor</th>
                    <th className="py-3 px-4">Action</th>
                    <th className="py-3 px-4">Target</th>
                    <th className="py-3 px-4">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40 text-xs">
                  {auditLogs?.map((log) => (
                    <tr key={log.id} className="hover:bg-muted/20">
                      <td className="py-3 px-4 font-bold text-foreground">{log.actor_name}</td>
                      <td className="py-3 px-4">
                        <span className="text-[10px] font-black uppercase bg-brand-500/10 text-brand-600 px-2 py-0.5 rounded-full">
                          {log.action}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono text-[10px] text-muted-foreground">
                        {log.target_type} ({log.target_id?.substring(0, 8)})
                      </td>
                      <td className="py-3 px-4 font-mono text-[10px] text-muted-foreground">
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}

                  {(!auditLogs || auditLogs.length === 0) && (
                    <tr>
                      <td colSpan={4} className="py-8 text-center text-xs font-bold text-muted-foreground">
                        No audit log entries recorded yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
