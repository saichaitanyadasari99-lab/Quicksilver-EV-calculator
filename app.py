"""
QuickSilver v4 — EV Powertrain Calculator
Full physics coupling: GVW/payload, grade, Cd/Area, tyres, DCIR → all affect motor, range, thermal.
"""
import streamlit as st
import math
import plotly.graph_objects as go

st.set_page_config(page_title="QuickSilver · EV Powertrain Calculator", layout="wide", page_icon="⚡")

st.markdown("""
<style>
  .block-container{padding-top:1.6rem;padding-bottom:0.8rem;}
  .stTabs [data-baseweb="tab-list"]{gap:6px;background:#E2E8F0;padding:8px;border-radius:12px;border:1px solid #CBD5E1;margin-bottom:10px;overflow-x:auto;scrollbar-width:thin;}
  .stTabs [data-baseweb="tab"]{height:46px;padding:0 16px;background:#FFFFFF;border:1px solid #94A3B8;border-radius:10px;font-weight:800;font-size:13px;color:#0F172A;box-shadow:0 1px 0 rgba(15,23,42,0.06);}
  .stTabs [data-baseweb="tab"]:hover{background:#E2E8F0;color:#0F172A;border-color:#64748B;}
  .stTabs [data-baseweb="tab"][aria-selected="true"]{color:#FFFFFF !important;border-color:transparent;box-shadow:0 8px 20px rgba(15,23,42,0.18);transform:translateY(-1px);}
  .stTabs [data-baseweb="tab"]:nth-child(1)[aria-selected="true"]{background:linear-gradient(135deg,#1D6EFB,#2563EB);} .stTabs [data-baseweb="tab"]:nth-child(2)[aria-selected="true"]{background:linear-gradient(135deg,#0284C7,#0369A1);} .stTabs [data-baseweb="tab"]:nth-child(3)[aria-selected="true"]{background:linear-gradient(135deg,#0EA5E9,#0284C7);} .stTabs [data-baseweb="tab"]:nth-child(4)[aria-selected="true"]{background:linear-gradient(135deg,#7C3AED,#6D28D9);} .stTabs [data-baseweb="tab"]:nth-child(5)[aria-selected="true"]{background:linear-gradient(135deg,#0D9488,#0F766E);} .stTabs [data-baseweb="tab"]:nth-child(6)[aria-selected="true"]{background:linear-gradient(135deg,#EA580C,#C2410C);} .stTabs [data-baseweb="tab"]:nth-child(7)[aria-selected="true"]{background:linear-gradient(135deg,#BE123C,#9F1239);} .stTabs [data-baseweb="tab"]:nth-child(8)[aria-selected="true"]{background:linear-gradient(135deg,#16A34A,#15803D);} .stTabs [data-baseweb="tab"]:nth-child(9)[aria-selected="true"]{background:linear-gradient(135deg,#4F46E5,#4338CA);} .stTabs [data-baseweb="tab"]:nth-child(10)[aria-selected="true"]{background:linear-gradient(135deg,#2563EB,#1D4ED8);} .stTabs [data-baseweb="tab"]:nth-child(11)[aria-selected="true"]{background:linear-gradient(135deg,#14B8A6,#0F766E);} .stTabs [data-baseweb="tab"]:nth-child(12)[aria-selected="true"]{background:linear-gradient(135deg,#F97316,#EA580C);} 
  .tabguide{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 10px 0;}
  .tabchip{font-size:11px;font-weight:700;padding:4px 9px;border-radius:999px;background:#F8FAFC;border:1px solid #CBD5E1;color:#334155;}
  .mc{background:white;border:1px solid #E2E8F0;border-radius:10px;padding:12px;border-top:3px solid #1D6EFB;margin-bottom:6px;}
  .mc.g{border-top-color:#10B981;} .mc.a{border-top-color:#F59E0B;} .mc.r{border-top-color:#EF4444;}
  .ml{font-size:10px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:.05em;}
  .mv{font-size:21px;font-weight:500;color:#0F172A;font-family:monospace;line-height:1.2;}
  .mu{font-size:10px;color:#94A3B8;}
  .sh{font-size:11px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px;margin-top:12px;border-bottom:1px solid #E2E8F0;padding-bottom:4px;}
  .infobox{background:#EFF4FF;border:1px solid #BFDBFE;border-radius:8px;padding:10px 14px;font-size:12px;color:#1e3a8a;margin-bottom:10px;}
  .warnbox{background:#FFFBEB;border:1px solid #FDE68A;border-radius:8px;padding:10px 14px;font-size:12px;color:#92400e;margin-bottom:10px;}
  .rolebox{background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:10px 12px;margin-bottom:8px;}
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════
# COLOURS & TINY HELPERS
# ════════════════════════════════════════════════════════════════════════
BLUE='#1D6EFB'; GREEN='#10B981'; AMBER='#F59E0B'; RED='#EF4444'; SLATE='#94A3B8'

def kw(w): return w/1000
def mc(label,value,unit,c=''):
    return f'<div class="mc {c}"><div class="ml">{label}</div><div class="mv">{value}</div><div class="mu">{unit}</div></div>'

def hex_to_rgba(hex_color, alpha):
    h = hex_color.lstrip('#')
    if len(h) != 6:
        return f'rgba(148,163,184,{alpha})'
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    return f'rgba({r},{g},{b},{alpha})'


LAYOUT = dict(margin=dict(l=8,r=8,t=32,b=8), plot_bgcolor='white', paper_bgcolor='white',
              font_size=11, legend_font_size=10,
              yaxis=dict(gridcolor='#F1F5F9'), xaxis=dict(gridcolor='#F1F5F9'))

def pbar(labels, vals, colors=None, title='', ylab='', h=270):
    fig = go.Figure(go.Bar(x=labels, y=vals, marker_color=colors or [BLUE]*len(vals),
                           marker_line_width=0, text=[f'{v:.1f}' for v in vals], textposition='outside'))
    fig.update_layout(title=title, height=h, yaxis_title=ylab, **LAYOUT)
    return fig

def pline(xs, yd, title='', xlab='', ylab='', h=270):
    colours=[BLUE,AMBER,GREEN,RED,SLATE]; dashes=['solid','dash','dot','dashdot','solid']
    fig = go.Figure()
    for i,(name,y) in enumerate(yd.items()):
        fig.add_trace(go.Scatter(x=xs,y=y,name=name,
                                 line=dict(color=colours[i%5],dash=dashes[i%5],width=2),mode='lines'))
    fig.update_layout(title=title, height=h, xaxis_title=xlab, yaxis_title=ylab, **LAYOUT)
    return fig

# ════════════════════════════════════════════════════════════════════════
# CORE PHYSICS ENGINE — everything flows from one calculate()
# ════════════════════════════════════════════════════════════════════════
def calculate(I):
    g = 9.81

    # Mass model: rated GVW + rated payload define kerb; operating payload sets active mass
    I = dict(I)
    I['gvwRated'] = I['gvw']
    I['payloadRated'] = I.get('payloadRated', I['payload'])
    kerb_mass = max(500.0, I['gvwRated'] - I['payloadRated'])
    gvw_effective = max(500.0, kerb_mass + I['payload'])
    overload_pct = (gvw_effective - I['gvwRated']) / max(1.0, I['gvwRated']) * 100
    I['gvw'] = gvw_effective


    # ── Atmosphere ──────────────────────────────────────────────────────
    P_atm = 101325 * math.exp(-I['altitude'] / 8500)
    T_K   = I['ambientTemp'] + 273.15
    rho   = P_atm / (287.05 * T_K)            # kg/m³

    # ── Tyre geometry ───────────────────────────────────────────────────
    r_rim    = (I['tyreDiam'] * 25.4) / 2      # mm
    sw       = I['tyreWidth'] * (I['tyreAspect'] / 100)   # mm sidewall
    r_static = (r_rim + sw) / 1000             # m
    r_dyn    = r_static * 0.963                # m loaded radius
    # Circumference → wheel RPM at top speed
    N_wheel  = (I['topSpeed'] / 3.6) / (2 * math.pi * r_dyn) * 60

    # ── Gear ratio ──────────────────────────────────────────────────────
    gearRatio = (I['motorMax'] / N_wheel) if I['gearMode']=='auto' else I['gearRatio']
    N_motor_at_top = gearRatio * N_wheel

    # ── Drivetrain efficiencies ─────────────────────────────────────────
    nm = I['motorEff']
    ng = I['gearEff']
    eta = nm * ng

    # ── Speed scalars ────────────────────────────────────────────────────
    v_top   = I['topSpeed']   / 3.6
    v_grade = I['gradeSpeed'] / 3.6
    v_60    = 60 / 3.6

    # ── Grade geometry ───────────────────────────────────────────────────
    theta = math.atan(I['grade'] / 100)
    sinT  = math.sin(theta)
    cosT  = math.cos(theta)

    # ── Road forces (grade climbing — worst case sizing) ─────────────────
    F_roll_grade = I['gvw'] * g * I['cr'] * cosT
    F_aero_grade = 0.5 * rho * I['cd'] * I['frontalArea'] * v_grade**2
    F_grade_N    = I['gvw'] * g * sinT
    F_total_grade = F_roll_grade + F_aero_grade + F_grade_N

    # ── Road forces (flat top speed — field-weakening check) ─────────────
    F_roll_flat = I['gvw'] * g * I['cr']
    F_aero_top  = 0.5 * rho * I['cd'] * I['frontalArea'] * v_top**2
    F_total_flat = F_roll_flat + F_aero_top

    # ── Wheel and motor power requirements ───────────────────────────────
    P_wheel_grade = F_total_grade * v_grade
    P_wheel_flat  = F_total_flat  * v_top

    P_req_cont_W   = P_wheel_grade / eta
    P_req_design_W = P_req_cont_W * 1.10           # +10% design margin

    # Acceleration requirement
    a_accel       = v_60 / I['accelTime']
    F_accel       = I['gvw'] * a_accel
    P_wheel_accel = (F_roll_flat + F_accel) * v_60
    P_req_accel_W = P_wheel_accel / eta
    P_req_peak_W  = max(P_req_design_W, P_req_accel_W)

    # ── User motor (what they spec'd) ────────────────────────────────────
    P_user_cont = I['motorCont'] * 1000
    P_user_peak = I['motorPeak'] * 1000
    T_user_peak = (P_user_peak * 60) / (2 * math.pi * I['motorBase'])
    T_user_cont = (P_user_cont * 60) / (2 * math.pi * I['motorBase'])

    # ── Wheel torque ─────────────────────────────────────────────────────
    # COUPLING: r_dyn from tyre params → T_req changes with tyre size
    T_req_grade_Nm = F_total_grade * r_dyn        # torque needed at wheel
    T_wheel_peak   = T_user_peak * gearRatio * ng  # torque available

    torque_margin  = (T_wheel_peak - T_req_grade_Nm) / T_req_grade_Nm * 100
    fw_margin      = (P_user_cont  - P_wheel_flat)   / P_wheel_flat   * 100

    motor_cont_ok  = P_user_cont >= P_req_design_W
    motor_peak_ok  = P_user_peak >= P_req_peak_W
    motor_speed_ok = N_motor_at_top <= I['motorMax']
    torque_ok      = T_wheel_peak  >= T_req_grade_Nm

    # ════════════════════════════════════════════════════════════════════
    # PHYSICS-BASED ENERGY MODEL
    # COUPLING: GVW, Cd, Area, Cr, tyre r_dyn, motor/gear η → kWh/km
    # ════════════════════════════════════════════════════════════════════
    #
    # kWh/km cruise = F[N] / (eta * 3600)    (unit check: N / (W/W * s/h) = Wh/m * 1000 = kWh/km)
    # Stop-go adds kinetic energy cost (partly recovered by regen)
    # Segment speeds representative of each duty type

    v_u = 35 / 3.6   # m/s — urban avg cruise speed
    v_t = 55 / 3.6   # m/s — transit avg
    v_h = max(v_grade + 5/3.6, min(I['topSpeed'] * 0.90, 75) / 3.6)  # highway

    # Road force at each speed (COUPLED to GVW, Cd, A, Cr)
    def road_force(v):
        return I['gvw']*g*I['cr'] + 0.5*rho*I['cd']*I['frontalArea']*v**2

    F_u = road_force(v_u)
    F_t = road_force(v_t)
    F_h = road_force(v_h)

    # Cruise energy (constant speed)
    e_cruise_u = F_u / (eta * 3600)
    e_cruise_t = F_t / (eta * 3600)
    e_cruise_h = F_h / (eta * 3600)

    # Stop-go kinetic penalty (net after regen) — COUPLED to GVW
    # Urban: ~2 stops/km from 35 km/h; regen recovers ~25% net
    KE_u = 0.5 * I['gvw'] * v_u**2   # J per stop
    KE_t = 0.5 * I['gvw'] * v_t**2
    stops_u = 1.5   # stops/km urban (delivery + traffic lights)
    stops_t = 0.3   # stops/km transit
    regen_frac = 0.40  # fraction of KE recovered by regen braking
    e_stopgo_u = stops_u * KE_u * (1 - regen_frac) / (eta * 3.6e6)   # kWh/km
    e_stopgo_t = stops_t * KE_t * (1 - regen_frac) / (eta * 3.6e6)

    # Segment energies are finalized below with aux-load calibration

    # Weighted duty-cycle energy (physics-based)
    v_u_kmh = max(10.0, v_u * 3.6)
    v_t_kmh = max(15.0, v_t * 3.6)
    v_h_kmh = max(20.0, v_h * 3.6)

    # Auxiliary load converted from kW to kWh/km by duty speed
    e_aux_u = I['auxKw'] / v_u_kmh
    e_aux_t = I['auxKw'] / v_t_kmh
    e_aux_h = I['auxKw'] / v_h_kmh

    eng_phys_urban   = e_cruise_u + e_stopgo_u + e_aux_u
    eng_phys_transit = e_cruise_t + e_stopgo_t + e_aux_t
    eng_phys_highway = e_cruise_h + e_aux_h

    # Also keep user's manual kWh/km as reference
    E_gross_duty_manual = (I['fracUrban']  * I['engUrban'] +
                           I['fracTransit'] * I['engTransit'] +
                           I['fracHighway'] * I['engHighway'])

    # Regen recovery (physics-based, COUPLED to drivetrain eta)
    regenChain = nm * ng * 0.95

    def duty_energy_terms(e_u, e_t, e_h):
        e_gross = (I['fracUrban'] * e_u +
                   I['fracTransit'] * e_t +
                   I['fracHighway'] * e_h)
        e_regen_avail = I['regenCapture'] * (I['fracUrban'] * e_u + I['fracTransit'] * e_t)
        e_regen = e_regen_avail * regenChain
        e_net = max(0.001, e_gross - e_regen)
        e_design_local = e_net * I['rwMargin'] * I['realWorldFactor']
        return e_gross, e_regen, e_net, e_design_local

    E_gross_duty_phys, E_regen_net, E_net_base, E_design = duty_energy_terms(
        eng_phys_urban, eng_phys_transit, eng_phys_highway
    )

    # Use calibrated physics model for sizing
    E_gross_duty = E_gross_duty_phys
    E_mission  = I['range'] * E_design

    res_fan   = 0.050 * 6
    res_route = E_mission * 0.02
    res_dcir  = E_mission * 0.02
    res_buf   = 0.25
    E_reserves = res_fan + res_route + res_dcir + res_buf
    E_usable   = E_mission + E_reserves

    socWindow = 1 - I['topGuard'] - I['botGuard']
    E_gross   = E_usable / max(0.01, socWindow)

    # ── Pack (from user config) ──────────────────────────────────────────
    packAh     = I['cellAh'] * I['parallelStr']
    V_pack_nom = I['seriesCells'] * 3.2          # LFP nominal 3.2V/cell
    V_pack_max = I['seriesCells'] * 3.65
    E_pack     = (V_pack_nom * packAh) / 1000    # kWh gross from config

    # ── Currents & C-rates ───────────────────────────────────────────────
    I_cruise = P_user_cont / V_pack_nom
    I_peak_A = P_user_peak / V_pack_nom
    I_dcfc   = (I['dcfcPower'] * 1000 * I['dcfcEff']) / V_pack_nom
    I_ac     = (I['obcPower']  * 1000 * I['obcEff'])  / V_pack_nom

    C_cruise = I_cruise / packAh
    C_peak   = I_peak_A / packAh
    C_dcfc   = I_dcfc   / packAh
    C_ac     = I_ac     / packAh

    # ════════════════════════════════════════════════════════════════════
    # DCIR COUPLING — voltage sag → available power → derating
    # ════════════════════════════════════════════════════════════════════
    R_pack = I['packDCIR']   # Ω (already converted from mΩ in sidebar)

    V_sag_cruise  = I_cruise * R_pack    # V drop at cruise
    V_sag_peak    = I_peak_A * R_pack    # V drop at peak
    V_sag_dcfc    = I_dcfc   * R_pack    # V drop during DCFC

    V_term_cruise = V_pack_nom - V_sag_cruise   # actual terminal voltage
    V_term_peak   = V_pack_nom - V_sag_peak
    V_term_dcfc   = V_pack_nom - V_sag_dcfc

    # Actual deliverable power at terminal voltage (COUPLED to DCIR)
    P_actual_cruise = V_term_cruise * I_cruise    # W
    P_actual_peak   = V_term_peak   * I_peak_A
    P_derate_pct    = (P_user_peak - P_actual_peak) / P_user_peak * 100 if P_user_peak > 0 else 0

    # DCFC acceptance: if sag is too large charger derates
    V_sag_pct_dcfc   = V_sag_dcfc / V_pack_nom * 100
    dcfc_derate_flag = V_sag_pct_dcfc > 5.0   # >5% sag → charger derates

    # Thermal — heat from DCIR (COUPLED: higher DCIR → more heat)
    Q_dcfc_W   = I_dcfc**2   * R_pack
    Q_cruise_W = I_cruise**2  * R_pack
    Q_peak_W   = I_peak_A**2  * R_pack
    Q_air_W    = rho * 0.05 * 1005 * 15     # air cooling capacity
    Q_net_pcm  = max(0, Q_peak_W - Q_air_W)
    m_pcm_min  = (Q_net_pcm * 30 * 10) / 175000
    m_pcm_corr = m_pcm_min * 2.0 * 1.3 * 1.5

    # Motor thermal
    Q_motor_cont_W = P_user_cont * (1 - nm)
    Q_motor_peak_W = P_user_peak * (1 - I['motorEffPeak'])
    T_winding      = I['ambientTemp'] + 20 + (Q_motor_cont_W * 0.00833)

    # ── Charging ────────────────────────────────────────────────────────
    t_ac_h    = E_usable / (I['obcPower'] * I['obcEff'])
    E_dcfc_ch = E_usable * 0.60
    t_dc_h    = E_dcfc_ch / (I['dcfcPower'] * I['dcfcEff'])
    t_dc_min  = t_dc_h * 60
    P_v2l     = 3680
    P_v2l_draw = P_v2l / I['obcEff']
    t_v2l_h   = E_usable / (P_v2l_draw / 1000)

    # ── Braking ─────────────────────────────────────────────────────────
    # COUPLED: top speed (from tyre+gear) → braking energy
    a_req          = v_top**2 / (2 * 50)    # decel over 50m
    mu_eq          = a_req / g
    F_brake_total  = I['gvw'] * a_req
    F_regen_brk    = 30000 / v_60
    a_regen        = F_regen_brk / I['gvw']
    F_friction_brk = F_brake_total - F_regen_brk

    # ── HV protection ───────────────────────────────────────────────────
    I_fault     = V_pack_max / max(0.001, R_pack)
    tau_pre     = -2 / math.log(0.05)
    R_precharge = tau_pre / 0.002
    E_cap       = 0.5 * 0.002 * (0.95 * V_pack_nom)**2
    R_iso_trip  = 100 * V_pack_max

    # ── LV ──────────────────────────────────────────────────────────────
    LV_load = 730
    t_agm_h = (60 * 13.8) / 145

    # ── Suspension — COUPLED to GVW ─────────────────────────────────────
    F_front     = I['gvw'] * g * 0.55
    F_rear      = I['gvw'] * g * 0.45
    m_spr_front = (F_front * 0.85) / g
    m_spr_rear  = (F_rear  * 0.85) / g
    k_front     = m_spr_front * (2 * math.pi * 1.20)**2
    k_rear      = m_spr_rear  * (2 * math.pi * 1.35)**2

    # ── Pack vs. target ─────────────────────────────────────────────────
    range_actual     = (E_pack * socWindow) / max(0.001, E_design)
    pack_margin_pct  = (E_pack - E_gross) / max(0.001, E_gross) * 100
    range_margin_pct = (range_actual - I['range']) / max(1, I['range']) * 100

    # ── Weight estimates ─────────────────────────────────────────────────
    w_pack_kg    = E_gross * 7.0
    w_motor_kg   = P_user_cont / 1000 * 3.0
    w_gearbox_kg = 0.8 * gearRatio

    # ── Design scores for radar ─────────────────────────────────────────
    def clamp(v,lo=0,hi=100): return max(lo,min(hi,v))
    score_range   = clamp(range_margin_pct + 50)
    score_motor   = clamp(torque_margin    + 50)
    score_speed   = clamp((I['motorMax'] - N_motor_at_top) / max(1,I['motorMax'])*100 + 30)
    score_thermal = clamp(100 - Q_net_pcm / max(1,Q_peak_W)*100)
    score_crate   = clamp((3 - C_cruise) / 3 * 100)
    score_pack    = clamp(pack_margin_pct  + 50)
    score_dcir    = clamp(100 - P_derate_pct * 5)   # new: DCIR health

    # ════════════════════════════════════════════════════════════════════
    # SENSITIVITY SWEEPS — all physics-coupled
    # ════════════════════════════════════════════════════════════════════

    # GVW sweep (COUPLED: affects rolling, grade force, accel, regen)
    gvw_sens = []
    for m in range(max(500, I['gvw']-1000), I['gvw']+1001, 200):
        F_g = m*g*I['cr'] + 0.5*rho*I['cd']*I['frontalArea']*v_u**2
        F_t2= m*g*I['cr'] + 0.5*rho*I['cd']*I['frontalArea']*v_t**2
        F_h2= m*g*I['cr'] + 0.5*rho*I['cd']*I['frontalArea']*v_h**2
        e_u2 = F_g/(eta*3600)  + stops_u*0.5*m*v_u**2*(1-regen_frac)/(eta*3.6e6) + e_aux_u
        e_t2 = F_t2/(eta*3600) + stops_t*0.5*m*v_t**2*(1-regen_frac)/(eta*3.6e6) + e_aux_t
        e_h2 = F_h2/(eta*3600) + e_aux_h
        _, _, _, e_d2 = duty_energy_terms(e_u2, e_t2, e_h2)
        rng2 = round((E_pack*socWindow)/max(0.001,e_d2))
        # Motor req at grade
        Fg2   = m*g*sinT; Fr2 = m*g*I['cr']*cosT
        P_req2= (Fr2 + F_aero_grade + Fg2)*v_grade/eta/1000
        gvw_sens.append({'gvw':m,'range':rng2,'motor_req_kw':round(P_req2*10)/10})

    # Payload sweep (subset of GVW sweep)
    payload_sens = []
    for adj in range(-1000, 1001, 200):
        pl   = max(0, I['payload'] + adj)
        m_veh= I['gvw'] - I['payload']
        m2   = m_veh + pl
        F_u2 = m2*g*I['cr'] + 0.5*rho*I['cd']*I['frontalArea']*v_u**2
        F_t2 = m2*g*I['cr'] + 0.5*rho*I['cd']*I['frontalArea']*v_t**2
        F_h2 = m2*g*I['cr'] + 0.5*rho*I['cd']*I['frontalArea']*v_h**2
        e_u2 = F_u2/(eta*3600) + stops_u*0.5*m2*v_u**2*(1-regen_frac)/(eta*3.6e6) + e_aux_u
        e_t2 = F_t2/(eta*3600) + stops_t*0.5*m2*v_t**2*(1-regen_frac)/(eta*3.6e6) + e_aux_t
        e_h2 = F_h2/(eta*3600) + e_aux_h
        _, _, _, e_d2 = duty_energy_terms(e_u2, e_t2, e_h2)
        payload_sens.append({'payload':pl,'range':round((E_pack*socWindow)/max(0.001,e_d2))})
    seen=set()
    payload_sens=[x for x in payload_sens if not(x['payload']in seen or seen.add(x['payload']))]
    payload_sens.sort(key=lambda x:x['payload'])

    # Cd sweep (COUPLED: affects aero power, range, motor req)
    cd_sens = []
    for cd_v in [0.25,0.30,0.35,0.40,0.42,0.45,0.50,0.55,0.60,0.70]:
        F_u2=I['gvw']*g*I['cr']+0.5*rho*cd_v*I['frontalArea']*v_u**2
        F_t2=I['gvw']*g*I['cr']+0.5*rho*cd_v*I['frontalArea']*v_t**2
        F_h2=I['gvw']*g*I['cr']+0.5*rho*cd_v*I['frontalArea']*v_h**2
        e_u2=F_u2/(eta*3600)+stops_u*0.5*I['gvw']*v_u**2*(1-regen_frac)/(eta*3.6e6)+e_aux_u
        e_t2=F_t2/(eta*3600)+stops_t*0.5*I['gvw']*v_t**2*(1-regen_frac)/(eta*3.6e6)+e_aux_t
        e_h2=F_h2/(eta*3600)+e_aux_h
        _, _, _, e_d2 = duty_energy_terms(e_u2, e_t2, e_h2)
        # grade motor req with this Cd
        Fa2=0.5*rho*cd_v*I['frontalArea']*v_grade**2
        P2=(F_roll_grade+Fa2+F_grade_N)*v_grade/eta/1000
        cd_sens.append({'cd':cd_v,'range':round((E_pack*socWindow)/max(0.001,e_d2)),
                        'motor_kw':round(P2*10)/10})

    # Grade sweep (COUPLED: affects motor req, torque, range on grades)
    grade_sens=[]
    for gr in [0,5,8,10,12,15,18,20,22,25,30]:
        thg=math.atan(gr/100)
        Fg=I['gvw']*g*math.sin(thg)
        Fr=I['gvw']*g*I['cr']*math.cos(thg)
        Fa=0.5*rho*I['cd']*I['frontalArea']*v_grade**2
        Pm=(Fr+Fa+Fg)*v_grade/eta/1000
        Tw=(Fr+Fa+Fg)*r_dyn   # wheel torque required
        grade_sens.append({'grade':gr,'motorPowerKW':round(Pm*10)/10,
                           'wheelTorqueNm':round(Tw),
                           'canClimb':Pm*1000<=P_user_cont})

    # Grade speed sweep — how climbing speed affects power req (GradeSpeed axis)
    grade_speed_sens=[]
    for vs_kmh in range(5, 51, 5):
        vs=vs_kmh/3.6
        Fa_vs=0.5*rho*I['cd']*I['frontalArea']*vs**2
        Pm_vs=(F_roll_grade+Fa_vs+F_grade_N)*vs/eta/1000
        grade_speed_sens.append({'speed':vs_kmh,'motorKW':round(Pm_vs*10)/10})

    # Ambient temperature sweep
    ambient_sens=[]
    for T in [5,10,15,20,25,30,35,40,45,50]:
        rho_T=P_atm/(287.05*(T+273.15))
        dFan = max(0,(T-30)*0.0003)   # fan energy increases above 30C
        F_u2=I['gvw']*g*I['cr']+0.5*rho_T*I['cd']*I['frontalArea']*v_u**2
        F_h2=I['gvw']*g*I['cr']+0.5*rho_T*I['cd']*I['frontalArea']*v_h**2
        e_u2=F_u2/(eta*3600)+stops_u*0.5*I['gvw']*v_u**2*(1-regen_frac)/(eta*3.6e6)+dFan+e_aux_u
        e_h2=F_h2/(eta*3600)+dFan+e_aux_h
        e_t2=(I['gvw']*g*I['cr']+0.5*rho_T*I['cd']*I['frontalArea']*v_t**2)/(eta*3600)+dFan+e_aux_t
        _, _, _, e_d2 = duty_energy_terms(e_u2, e_t2, e_h2)
        ambient_sens.append({'temp':T,'range':round((E_pack*socWindow)/max(0.001,e_d2))})

    # Speed-power curve (COUPLED: GVW, Cd, A, motor eff, gear eff)
    speed_power_sens=[]
    for v_kmh in range(5, min(I['topSpeed']+21,121), 5):
        vm=v_kmh/3.6
        Fr2=I['gvw']*g*I['cr']
        Fa2=0.5*rho*I['cd']*I['frontalArea']*vm**2
        Pw=(Fr2+Fa2)*vm
        speed_power_sens.append({'speed':v_kmh,
                                  'wheelPowerKW':round(Pw/100)/10,
                                  'motorPowerKW':round(Pw/(eta)/100)/10,
                                  'rollKW':round(Fr2*vm/1000,2),
                                  'aeroKW':round(Fa2*vm/1000,2)})

    # DCIR sweep — shows how pack resistance affects heat, voltage sag, power
    dcir_sens=[]
    for dcir_mo in [5,10,15,20,30,50,75,100,150,200]:
        R2=dcir_mo/1000
        V_sag2=I_peak_A*R2
        P_act2=(V_pack_nom-V_sag2)*I_peak_A/1000
        heat2=I_peak_A**2*R2
        dcir_sens.append({'dcir':dcir_mo,'vsag':round(V_sag2,1),
                          'power_kw':round(P_act2,1),'heat_w':round(heat2)})

    # Tyre radius sweep — shows effect on N_wheel, gear ratio, torque req
    tyre_sens=[]
    for r_mm in range(280, 381, 10):   # r_dyn range 280–380 mm
        r2=r_mm/1000
        N_w2=(v_top/(2*math.pi*r2))*60
        gr2=I['motorMax']/N_w2  # auto mode gear ratio
        T_req2=F_total_grade*r2
        tyre_sens.append({'r_dyn_mm':r_mm,'N_wheel':round(N_w2),
                          'gear_ratio_auto':round(gr2,2),'T_req_Nm':round(T_req2)})

    # Gear ratio sweep
    gear_sens=[]
    for gr in [6,6.5,7,7.5,8,8.3,8.6,8.85,9.1,9.5,10,11,12]:
        T_wh=T_user_peak*gr*ng
        N_top=gr*N_wheel
        gear_sens.append({'ratio':gr,'wheelTorque':round(T_wh),
                          'motorRPMAtTop':round(N_top),
                          'ok':N_top<=I['motorMax'] and T_wh>=T_req_grade_Nm})

    return dict(
        # Atmosphere & geometry
        rho=rho, r_static=r_static, r_dyn=r_dyn, N_wheel=N_wheel,
        theta=theta, sinT=sinT, cosT=cosT, gearRatio=gearRatio, N_motor_at_top=N_motor_at_top,
        # Forces
        F_roll_flat=F_roll_flat, F_roll_grade=F_roll_grade,
        F_aero_top=F_aero_top,  F_aero_grade=F_aero_grade, F_grade_N=F_grade_N,
        F_total_grade=F_total_grade, F_total_flat=F_total_flat,
        # Power requirements
        P_wheel_grade=P_wheel_grade, P_wheel_flat=P_wheel_flat,
        P_req_cont_W=P_req_cont_W,   P_req_design_W=P_req_design_W,
        P_req_peak_W=P_req_peak_W,   P_req_accel_W=P_req_accel_W,
        a_accel=a_accel, F_accel=F_accel, P_wheel_accel=P_wheel_accel,
        # Motor
        P_user_cont=P_user_cont, P_user_peak=P_user_peak,
        T_user_peak=T_user_peak, T_user_cont=T_user_cont,
        T_wheel_peak=T_wheel_peak, T_req_grade_Nm=T_req_grade_Nm,
        torque_margin=torque_margin, fw_margin=fw_margin,
        motor_cont_ok=motor_cont_ok, motor_peak_ok=motor_peak_ok,
        motor_speed_ok=motor_speed_ok, torque_ok=torque_ok,
        # Physics-based energy model
        eng_phys_urban=eng_phys_urban, eng_phys_transit=eng_phys_transit, eng_phys_highway=eng_phys_highway,
        E_gross_duty_phys=E_gross_duty_phys, E_gross_duty_manual=E_gross_duty_manual,
        E_gross_duty=E_gross_duty,
        e_aux_u=e_aux_u, e_aux_t=e_aux_t, e_aux_h=e_aux_h,
        E_regen_net=E_regen_net, E_net_base=E_net_base, E_design=E_design,
        E_mission=E_mission, E_reserves=E_reserves,
        res_fan=res_fan, res_route=res_route, res_dcir=res_dcir, res_buf=res_buf,
        E_usable=E_usable, socWindow=socWindow, E_gross=E_gross,
        regen_capture=I['regenCapture'], real_world_factor=I['realWorldFactor'], aux_kw=I['auxKw'],
        # Pack
        V_pack_nom=V_pack_nom, packAh=packAh, E_pack=E_pack, V_pack_max=V_pack_max,
        I_cruise=I_cruise, I_peak_A=I_peak_A, I_dcfc=I_dcfc, I_ac=I_ac,
        C_cruise=C_cruise, C_peak=C_peak, C_dcfc=C_dcfc, C_ac=C_ac,
        # DCIR / voltage sag
        R_pack=R_pack, V_sag_cruise=V_sag_cruise, V_sag_peak=V_sag_peak, V_sag_dcfc=V_sag_dcfc,
        V_term_cruise=V_term_cruise, V_term_peak=V_term_peak, V_term_dcfc=V_term_dcfc,
        P_actual_cruise=P_actual_cruise, P_actual_peak=P_actual_peak, P_derate_pct=P_derate_pct,
        V_sag_pct_dcfc=V_sag_pct_dcfc, dcfc_derate_flag=dcfc_derate_flag,
        # Thermal
        Q_dcfc_W=Q_dcfc_W, Q_cruise_W=Q_cruise_W, Q_peak_W=Q_peak_W,
        Q_air_W=Q_air_W, Q_net_pcm=Q_net_pcm, m_pcm_min=m_pcm_min, m_pcm_corr=m_pcm_corr,
        Q_motor_cont_W=Q_motor_cont_W, Q_motor_peak_W=Q_motor_peak_W, T_winding=T_winding,
        # Charging
        t_ac_h=t_ac_h, t_dc_min=t_dc_min, t_v2l_h=t_v2l_h,
        P_v2l=P_v2l, P_v2l_draw=P_v2l_draw, E_dcfc_ch=E_dcfc_ch,
        # Braking & HV
        a_req=a_req, mu_eq=mu_eq, F_brake_total=F_brake_total,
        F_regen_brk=F_regen_brk, a_regen=a_regen, F_friction_brk=F_friction_brk,
        I_fault=I_fault, R_precharge=R_precharge, E_cap=E_cap, R_iso_trip=R_iso_trip,
        # LV / chassis
        t_agm_h=t_agm_h, LV_load=LV_load,
        F_front=F_front, F_rear=F_rear, k_front=k_front, k_rear=k_rear,
        # Range / pack adequacy
        range_actual=range_actual, pack_margin_pct=pack_margin_pct, range_margin_pct=range_margin_pct,
        w_pack_kg=w_pack_kg, w_motor_kg=w_motor_kg, w_gearbox_kg=w_gearbox_kg,
        # Radar scores
        score_range=score_range, score_motor=score_motor, score_speed=score_speed,
        score_thermal=score_thermal, score_crate=score_crate,
        score_pack=score_pack, score_dcir=score_dcir,
        # Sensitivity data
        payload_sens=payload_sens, gvw_sens=gvw_sens, cd_sens=cd_sens,
        grade_sens=grade_sens, grade_speed_sens=grade_speed_sens,
        ambient_sens=ambient_sens, speed_power_sens=speed_power_sens,
        dcir_sens=dcir_sens, tyre_sens=tyre_sens, gear_sens=gear_sens,
        # Segment speeds (for display)
        v_u_kmh=v_u_kmh, v_t_kmh=v_t_kmh, v_h_kmh=v_h_kmh,
        ng=ng,
        gvw_effective=gvw_effective, gvw_rated=I['gvwRated'],
        payload_operating=I['payload'], payload_rated=I['payloadRated'],
        kerb_mass=kerb_mass, overload_pct=overload_pct,
    )

# ════════════════════════════════════════════════════════════════════════
# SIDEBAR INPUTS
# ════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div style="background:#0F172A;color:white;padding:10px 16px;border-radius:8px;font-weight:700;font-size:15px;margin-bottom:12px;">⚡ QuickSilver v4 <span style="font-size:11px;font-weight:400;color:#94A3B8;">LFP SCV Calculator</span></div>', unsafe_allow_html=True)

    st.markdown('<div class="sh">🚗 Vehicle & Mission</div>', unsafe_allow_html=True)
    c1,c2=st.columns(2)
    gvw         = c1.number_input('Rated GVW (kg)',      value=3500,min_value=500, max_value=12000,step=50, help='Homologated gross vehicle weight at rated load condition.')
    payload_rated = c2.number_input('Rated Payload (kg)', value=1400,min_value=0,   max_value=6000,step=50, help='Payload used for rated vehicle configuration and kerb-mass derivation.')
    payload     = c1.number_input('Operating Payload (kg)',  value=1000,min_value=0,   max_value=7000,step=50, help='Actual payload for current trip simulation; can be underload or overload.')
    range_km    = c2.number_input('Range Target (km)',    value=180, min_value=50,  max_value=600, step=10, help='Mission distance target used for pack sizing and compliance checks.')
    top_speed   = c1.number_input('Top Speed (km/h)',value=80,min_value=30, max_value=160, step=5, help='Maximum vehicle speed target on flat road.')
    grade       = c1.number_input('Grade (%)',     value=22.0,min_value=0.0, max_value=50.0,step=0.5, help='Road grade target for climbing capability checks.')
    grade_speed = c2.number_input('Grade Spd (km/h)',value=20,min_value=5,  max_value=60,  step=5, help='Sustained climbing speed at selected grade.')
    accel_time  = c1.number_input('0→60 time (s)',value=18.0, min_value=5.0,max_value=60.0,step=0.5, help='Acceleration target from standstill to 60 km/h.')
    ambient     = c2.number_input('Ambient (°C)', value=45,   min_value=-20, max_value=55,  step=1, help='Ambient temperature for thermal and air-density effects.')
    altitude    = st.number_input('Altitude (m ASL)',value=200,min_value=0, max_value=3000,step=50, help='Operating altitude above sea level; affects air density.')

    st.markdown('<div class="sh">💨 Aero & Tyres</div>', unsafe_allow_html=True)
    c1,c2=st.columns(2)
    cd           = c1.number_input('Cd',          value=0.42,min_value=0.2,max_value=1.5,step=0.01,format='%.2f', help='Aerodynamic drag coefficient.')
    frontal_area = c2.number_input('Area A (m²)', value=3.8, min_value=1.0,max_value=10.0,step=0.1, help='Effective frontal area used in aero drag force.')
    cr           = st.number_input('Rolling Resist Cr',value=0.012,min_value=0.005,max_value=0.05,step=0.001,format='%.3f', help='Rolling resistance coefficient of tyres/road contact.')
    c1,c2=st.columns(2)
    tyre_width   = c1.number_input('Tyre Width (mm)',  value=195,min_value=100,max_value=400,step=5, help='Nominal tyre section width.')
    tyre_aspect  = c2.number_input('Aspect Ratio (%)', value=70, min_value=25, max_value=100,step=5, help='Tyre sidewall ratio: sidewall height as % of width.')
    tyre_diam    = st.number_input('Rim Diam (inch)',  value=15, min_value=10, max_value=24, step=1, help='Wheel rim diameter.')

    st.markdown('<div class="sh">⚙️ Gear Ratio</div>', unsafe_allow_html=True)
    gear_mode  = st.selectbox('Mode',['manual','auto'],index=0, help='Auto computes gear ratio from top-speed and motor max rpm.')
    gear_ratio = st.number_input('Gear Ratio i (:1)',value=8.85,min_value=3.0,max_value=20.0,step=0.05,format='%.2f',disabled=(gear_mode=='auto'), help='Final drive ratio between motor and wheel speed.')
    gear_eff   = st.number_input('Gear η_g',value=0.97,min_value=0.8,max_value=1.0,step=0.01,format='%.2f', help='Gearbox mechanical efficiency.')

    st.markdown('<div class="sh">🔧 Motor Spec</div>', unsafe_allow_html=True)
    c1,c2=st.columns(2)
    motor_cont    = c1.number_input('Continuous (kW)',value=40,  min_value=5,  max_value=200, step=5, help='Continuous motor power rating.')
    motor_peak    = c2.number_input('Peak 30s (kW)',  value=80,  min_value=5,  max_value=400, step=5, help='Short-duration peak motor power (30s).')
    motor_base_rpm= c1.number_input('Base rpm',       value=3000,min_value=500,max_value=8000,step=100, help='Motor base speed where constant-torque region ends.')
    motor_max_rpm = c2.number_input('Max rpm',        value=6000,min_value=1000,max_value=20000,step=100, help='Maximum allowable motor speed.')
    motor_eff     = c1.number_input('η cont',         value=0.95,min_value=0.7,max_value=0.99,step=0.01,format='%.2f', help='Motor efficiency under peak operation.')
    motor_eff_pk  = c2.number_input('η peak',         value=0.92,min_value=0.7,max_value=0.99,step=0.01,format='%.2f', help='Motor efficiency in continuous operation.')

    st.markdown('<div class="sh">🔋 Battery Pack</div>', unsafe_allow_html=True)
    c1,c2=st.columns(2)
    series_cells  = c1.number_input('Series (S)',    value=96,min_value=20, max_value=300,step=4, help='Number of cells in series in the traction pack.')
    parallel_str  = c2.number_input('Parallel (P)',  value=2, min_value=1,  max_value=10, step=1, help='Number of parallel strings in the pack.')
    cell_ah       = c1.number_input('Cell Ah',       value=40,min_value=10, max_value=300,step=5, help='Cell capacity in ampere-hours.')
    pack_dcir_mo  = c2.number_input('Pack DCIR (mΩ)',value=20,min_value=1,  max_value=200,step=1, help='Total pack DC internal resistance.')
    top_guard     = c1.number_input('Top Guard (%)', value=4.0,min_value=0.0,max_value=15.0,step=0.1, help='Top state-of-charge reserve not used in mission.')
    bot_guard     = c2.number_input('Bot Guard (%)', value=3.7,min_value=0.0,max_value=15.0,step=0.1, help='Bottom state-of-charge reserve not used in mission.')

    st.markdown('<div class="sh">🔄 Duty Cycle (Manual Reference)</div>', unsafe_allow_html=True)
    st.caption('Used as reference; physics model drives sizing automatically')
    c1,c2=st.columns(2)
    frac_urban   = c1.number_input('Urban frac',   value=0.55,min_value=0.0,max_value=1.0,step=0.05,format='%.2f', help='Fraction of duty cycle spent in urban driving.')
    eng_urban    = c2.number_input('Urban kWh/km', value=0.140,min_value=0.05,max_value=0.5,step=0.005,format='%.3f', help='Manual reference energy for urban segment.')
    frac_transit = c1.number_input('Transit frac', value=0.20,min_value=0.0,max_value=1.0,step=0.05,format='%.2f', help='Fraction of duty cycle spent in transit driving.')
    eng_transit  = c2.number_input('Transit kWh/km',value=0.110,min_value=0.05,max_value=0.4,step=0.005,format='%.3f', help='Manual reference energy for transit segment.')
    frac_highway = c1.number_input('Highway frac', value=0.25,min_value=0.0,max_value=1.0,step=0.05,format='%.2f', help='Fraction of duty cycle spent in highway driving.')
    eng_highway  = c2.number_input('Highway kWh/km',value=0.100,min_value=0.05,max_value=0.4,step=0.005,format='%.3f', help='Manual reference energy for highway segment.')
    rw_margin    = st.number_input('RW Margin x',  value=1.00,min_value=0.95,max_value=2.0,step=0.01,format='%.2f', help='Real-world mission margin multiplier applied to net energy.')
    c1,c2=st.columns(2)
    real_world_factor = c1.number_input('Real-world factor', value=0.98,min_value=0.85,max_value=1.60,step=0.01,format='%.2f', help='Calibration multiplier to align model with field data.')
    regen_capture     = c2.number_input('Regen capture frac', value=0.28,min_value=0.00,max_value=0.60,step=0.01,format='%.2f', help='Fraction of urban+transit braking energy captured by regen.')
    aux_kw            = st.number_input('Aux load (kW)', value=0.4,min_value=0.0,max_value=8.0,step=0.1,format='%.1f', help='Continuous auxiliary electrical load (HVAC, electronics, pumps).')
    st.caption('Calibration knobs for real-world fleets; no fixed load-to-range relation is hardcoded.')

    st.markdown('<div class="sh">Charging</div>', unsafe_allow_html=True)
    c1,c2=st.columns(2)
    obc_power  = c1.number_input('OBC Power (kW)',value=7.2,min_value=1.0, max_value=22.0, step=0.1, help='AC onboard charger power rating.')
    obc_eff    = c2.number_input('OBC η',         value=0.92,min_value=0.7,max_value=0.99, step=0.01,format='%.2f', help='Onboard charger efficiency.')
    dcfc_power = c1.number_input('DCFC (kW)',     value=25,  min_value=10,  max_value=350,  step=5, help='DC fast charge power level.')
    dcfc_eff   = c2.number_input('DCFC η',        value=0.95,min_value=0.8,max_value=0.99, step=0.01,format='%.2f', help='DC fast charging efficiency.')

    st.markdown("---")
    st.button('▶  Calculate', type='primary', use_container_width=True)

# ════════════════════════════════════════════════════════════════════════
# RUN CALCULATION
# ════════════════════════════════════════════════════════════════════════
I = dict(
    gvw=gvw, payload=payload, range=range_km, topSpeed=top_speed,
    grade=grade, gradeSpeed=grade_speed, accelTime=accel_time,
    ambientTemp=ambient, altitude=altitude,
    cd=cd, frontalArea=frontal_area, cr=cr,
    tyreWidth=tyre_width, tyreAspect=tyre_aspect, tyreDiam=tyre_diam,
    gearMode=gear_mode, gearRatio=gear_ratio, gearEff=gear_eff,
    motorCont=motor_cont, motorPeak=motor_peak,
    motorBase=motor_base_rpm, motorMax=motor_max_rpm,
    motorEff=motor_eff, motorEffPeak=motor_eff_pk,
    seriesCells=series_cells, parallelStr=parallel_str,
    cellAh=cell_ah, packDCIR=pack_dcir_mo/1000,
    topGuard=top_guard/100, botGuard=bot_guard/100,
    fracUrban=frac_urban,   engUrban=eng_urban,
    fracTransit=frac_transit, engTransit=eng_transit,
    fracHighway=frac_highway, engHighway=eng_highway,
    rwMargin=rw_margin,
    realWorldFactor=real_world_factor, regenCapture=regen_capture, auxKw=aux_kw,
    payloadRated=payload_rated,
    obcPower=obc_power, obcEff=obc_eff,
    dcfcPower=dcfc_power, dcfcEff=dcfc_eff,
)
try:
    R = calculate(I)
except Exception as e:
    st.error(f"Calculation error: {e}")
    import traceback; st.code(traceback.format_exc())
    st.stop()

# ════════════════════════════════════════════════════════════════════════
# TABS
# ════════════════════════════════════════════════════════════════════════
section_labels = [
    "Overview","Road","Battery","Drive",
    "Charging","Thermal","Safety","Chassis","Sensitivity",
    "Engineer","Customer","PM"
]
active_section = st.radio("Section", section_labels, index=0, horizontal=True)
st.caption("Horizontal section selector enabled.")

# ────────────────────────────────────────────────────────────────────────
# TAB 1 — OVERVIEW
# ────────────────────────────────────────────────────────────────────────
if active_section == "Overview":
    all_checks=[R['range_actual']>=range_km, R['torque_margin']>0, R['motor_speed_ok'],
                R['motor_cont_ok'], R['motor_peak_ok'], R['E_pack']>=R['E_gross'],
                R['t_ac_h']<5, R['t_dc_min']<60, R['C_cruise']<3, R['T_winding']<155]
    n_pass=sum(all_checks); n_total=len(all_checks)
    bc=GREEN if n_pass==n_total else (AMBER if n_pass>=n_total-2 else RED)
    bt="✅ ALL SYSTEMS GO" if n_pass==n_total else (f"⚠ {n_total-n_pass} ITEM(S) NEED ATTENTION" if n_pass>=n_total-2 else f"❌ {n_total-n_pass} CRITICAL FAILURES")
    st.markdown(f'<div style="background:{bc}18;border:2px solid {bc};border-radius:12px;padding:12px 18px;margin-bottom:12px;display:flex;align-items:center;justify-content:space-between;"><div style="font-size:14px;font-weight:800;color:{bc};">{bt}</div><div style="font-size:12px;color:#475569;font-weight:600;">{n_pass}/{n_total} checks passed &nbsp;|&nbsp; Actual range {R["range_actual"]:.0f} km &nbsp;|&nbsp; Pack margin {R["pack_margin_pct"]:+.1f}%</div></div>', unsafe_allow_html=True)

    # Physics model info box
    st.markdown(f'<div class="infobox"><b>Physics Model Active:</b> Energy from road load + payload-coupled mass. Active mass {R["gvw_effective"]:.0f} kg (rated {R["gvw_rated"]:.0f} kg, payload {R["payload_operating"]:.0f}/{R["payload_rated"]:.0f} kg, overload {R["overload_pct"]:+.1f}%). Physics: Urban {R["eng_phys_urban"]*1000:.1f} Wh/km | Transit {R["eng_phys_transit"]*1000:.1f} Wh/km | Highway {R["eng_phys_highway"]*1000:.1f} Wh/km | Cal: regen {R["regen_capture"]*100:.0f}% | aux {R["aux_kw"]:.1f} kW | RW x{R["real_world_factor"]:.2f}</div>', unsafe_allow_html=True)

    # Compliance cards
    compliance=[
        ("Actual Range",     f"{R['range_actual']:.0f} km", f"Target ≥{range_km} km ({R['range_margin_pct']:+.1f}%)", R['range_actual']>=range_km),
        ("Grade Climbing",   f"{grade}%",                    f"Torque margin {R['torque_margin']:.1f}%",               R['torque_margin']>0),
        ("Top Speed",        f"{top_speed} km/h",            f"Motor @ {R['N_motor_at_top']:.0f} rpm",                 R['motor_speed_ok']),
        ("Motor Continuous", f"{kw(R['P_user_cont']):.1f} kW", f"Need ≥{kw(R['P_req_design_W']):.1f} kW",            R['motor_cont_ok']),
        ("Motor Peak",       f"{kw(R['P_user_peak']):.1f} kW", f"Need ≥{kw(R['P_req_peak_W']):.1f} kW",              R['motor_peak_ok']),
        ("Pack Adequacy",    f"{R['E_pack']:.1f} kWh",       f"Need ≥{R['E_gross']:.1f} kWh ({R['pack_margin_pct']:+.1f}%)", R['E_pack']>=R['E_gross']),
        ("AC Charge",        f"{R['t_ac_h']:.1f} h",         "0→100%",                                                 R['t_ac_h']<5),
        ("DC Fast Charge",   f"{R['t_dc_min']:.0f} min",     "20→80%",                                                 R['t_dc_min']<60),
        ("Cruise C-rate",    f"{R['C_cruise']:.2f} C",       "LFP limit 3 C",                                          R['C_cruise']<3),
        ("Winding Temp",     f"{R['T_winding']:.0f} °C",     "Class F limit 155°C",                                    R['T_winding']<155),
    ]
    cols=st.columns(5)
    for i,(lbl,val,sub,ok) in enumerate(compliance):
        cols[i%5].markdown(mc(lbl,val,sub,'g' if ok else 'r'), unsafe_allow_html=True)

    st.markdown("---")
    c1,c2,c3=st.columns([1.1,1.1,0.8])
    with c1:
        radar_cats=['Range','Motor','Speed','Thermal','C-rate','Pack','DCIR']
        radar_vals=[R['score_range'],R['score_motor'],R['score_speed'],R['score_thermal'],R['score_crate'],R['score_pack'],R['score_dcir']]
        fig_r=go.Figure(go.Scatterpolar(r=radar_vals+[radar_vals[0]],theta=radar_cats+[radar_cats[0]],
                                         fill='toself',fillcolor='rgba(29,110,251,0.18)',
                                         line=dict(color=BLUE,width=2),marker=dict(size=5,color=BLUE)))
        fig_r.update_layout(polar=dict(radialaxis=dict(range=[0,100],tickfont_size=8,gridcolor='#E2E8F0'),
                                        angularaxis=dict(tickfont_size=10)),
                             title=dict(text='Design Health Radar',font_size=13),
                             height=290,margin=dict(l=20,r=20,t=40,b=10),paper_bgcolor='white',showlegend=False)
        st.plotly_chart(fig_r,use_container_width=True)
    with c2:
        st.plotly_chart(pbar(
            ['Grade\nLoad','Flat\nTop','Accel\nPeak','Motor\nCont','Motor\nPeak'],
            [kw(R['P_wheel_grade']),kw(R['P_wheel_flat']),kw(R['P_req_peak_W']),kw(R['P_user_cont']),kw(R['P_user_peak'])],
            colors=[BLUE,'#64B5F6',AMBER,GREEN,'#34D399'],title='Power Budget (kW)',ylab='kW',h=290
        ),use_container_width=True)
    with c3:
        pack_pct=min(200,max(0,R['E_pack']/max(0.1,R['E_gross'])*100))
        fig_g=go.Figure(go.Indicator(
            mode="gauge+number+delta",value=R['E_pack'],
            delta={'reference':R['E_gross'],'valueformat':'.1f','suffix':' kWh'},
            gauge={'axis':{'range':[0,R['E_gross']*1.5],'ticksuffix':' kWh','tickfont':{'size':8}},
                   'bar':{'color':GREEN if pack_pct>=100 else RED,'thickness':0.6},
                   'bgcolor':'white',
                   'steps':[{'range':[0,R['E_gross']],'color':'#FEE2E2'},
                             {'range':[R['E_gross'],R['E_gross']*1.5],'color':'#ECFDF5'}],
                   'threshold':{'line':{'color':RED,'width':3},'thickness':0.75,'value':R['E_gross']}},
            number={'suffix':' kWh','font':{'size':20}},
            title={'text':f"Pack Energy<br><span style='font-size:10px'>Need ≥{R['E_gross']:.1f} kWh</span>",'font':{'size':12}},
        ))
        fig_g.update_layout(height=290,margin=dict(l=10,r=10,t=40,b=10),paper_bgcolor='white')
        st.plotly_chart(fig_g,use_container_width=True)

    # Row 2: energy pie + efficiency chain
    c1,c2=st.columns(2)
    with c1:
        fig_pie=go.Figure(go.Pie(
            labels=['Mission','Fan','Route','DCIR','Arrival'],
            values=[round(R['E_mission'],1),round(R['res_fan'],2),round(R['res_route'],2),round(R['res_dcir'],2),round(R['res_buf'],2)],
            hole=0.45,marker_colors=[BLUE,AMBER,GREEN,RED,'#64B5F6'],textfont_size=10,textinfo='label+percent'))
        fig_pie.update_layout(title='Usable Energy Breakdown',height=270,margin=dict(l=0,r=0,t=30,b=0),
                              paper_bgcolor='white',showlegend=False)
        st.plotly_chart(fig_pie,use_container_width=True)
    with c2:
        # Physics vs Manual comparison bar
        seg_labels=['Urban\nPhysics','Transit\nPhysics','Highway\nPhysics','Urban\nManual','Transit\nManual','Highway\nManual']
        seg_vals=[R['eng_phys_urban']*1000,R['eng_phys_transit']*1000,R['eng_phys_highway']*1000,
                  eng_urban*1000,eng_transit*1000,eng_highway*1000]
        seg_colors=[BLUE,BLUE,BLUE,AMBER,AMBER,AMBER]
        st.plotly_chart(pbar(seg_labels,seg_vals,colors=seg_colors,
                             title='Physics vs Manual Energy (Wh/km)',ylab='Wh/km',h=270),use_container_width=True)

# ────────────────────────────────────────────────────────────────────────
# TAB 2 — ROAD LOAD
# ────────────────────────────────────────────────────────────────────────
if active_section == "Road":
    # KPI row
    kpis=[("Roll Resist (flat)",f"{R['F_roll_flat']:.0f}","N"),
          ("Aero Drag (top spd)",f"{R['F_aero_top']:.0f}","N"),
          ("Grade Force",f"{R['F_grade_N']:.0f}",f"N at {grade}%"),
          ("Total (grade)",f"{R['F_total_grade']:.0f}","N"),
          ("Wheel Pwr (grade)",f"{kw(R['P_wheel_grade']):.1f}","kW ← sizing"),
          ("Wheel Pwr (flat)",f"{kw(R['P_wheel_flat']):.1f}","kW ← FW check")]
    cols=st.columns(6)
    for i,(l,v,u) in enumerate(kpis): cols[i].markdown(mc(l,v,u),unsafe_allow_html=True)

    st.markdown(f"""
| Parameter | Formula | Value |
|---|---|---|
| Air density ρ | 101325·e^(−{altitude}/8500) / (287.05·{ambient+273:.0f}) | **{R['rho']:.3f} kg/m³** |
| Tyre r_dyn | rim+sidewall = {tyre_diam}×25.4/2 + {tyre_width}×{tyre_aspect/100} = {R['r_static']*1000:.0f} mm × 0.963 | **{R['r_dyn']*1000:.0f} mm** |
| N_wheel at {top_speed} km/h | ({top_speed}/3.6) / (2π × {R['r_dyn']:.3f}) × 60 | **{R['N_wheel']:.0f} rpm** |
| Grade angle θ | arctan({grade}/100) | **{math.degrees(R['theta']):.1f}°** |
| F_roll (flat) | {gvw} × 9.81 × {cr} | **{R['F_roll_flat']:.0f} N** |
| F_aero at {top_speed} km/h | ½ × {R['rho']:.3f} × {cd} × {frontal_area} × ({top_speed/3.6:.1f})² | **{R['F_aero_top']:.0f} N** |
| F_grade | {gvw} × 9.81 × sin({math.degrees(R['theta']):.1f}°) | **{R['F_grade_N']:.0f} N** |
| **F_total (grade)** | roll+aero+grade | **{R['F_total_grade']:.0f} N** |
| **P_wheel (grade)** | {R['F_total_grade']:.0f} × {grade_speed/3.6:.2f} m/s | **{kw(R['P_wheel_grade']):.2f} kW ★** |
| P_wheel (flat) | {R['F_total_flat']:.0f} × {top_speed/3.6:.2f} m/s | **{kw(R['P_wheel_flat']):.2f} kW** |
""")

    c1,c2=st.columns(2)
    with c1:
        # Speed vs force breakdown (stacked: roll + aero)
        spd_x=[d['speed'] for d in R['speed_power_sens']]
        fig_f=go.Figure()
        fig_f.add_trace(go.Scatter(x=spd_x,y=[d['rollKW'] for d in R['speed_power_sens']],
                                    name='Rolling (kW)',fill='tozeroy',fillcolor='rgba(16,185,129,0.2)',
                                    line=dict(color=GREEN,width=2)))
        fig_f.add_trace(go.Scatter(x=spd_x,y=[d['aeroKW'] for d in R['speed_power_sens']],
                                    name='Aero (kW)',fill='tonexty',fillcolor='rgba(29,110,251,0.2)',
                                    line=dict(color=BLUE,width=2)))
        fig_f.add_trace(go.Scatter(x=spd_x,y=[d['wheelPowerKW'] for d in R['speed_power_sens']],
                                    name='Total Wheel (kW)',line=dict(color=RED,width=2,dash='dash')))
        fig_f.update_layout(title='Speed vs Force Components (kW)',height=280,
                             xaxis_title='Speed (km/h)',yaxis_title='Power (kW)',**LAYOUT)
        st.plotly_chart(fig_f,use_container_width=True)
    with c2:
        # Motor power required vs speed
        st.plotly_chart(pline(spd_x,
            {'Wheel Power (kW)':[d['wheelPowerKW'] for d in R['speed_power_sens']],
             'Motor Power Req (kW)':[d['motorPowerKW'] for d in R['speed_power_sens']],
             f'Motor Cont ({motor_cont} kW)':[motor_cont for _ in spd_x]},
            title='Motor Power Requirement vs Speed',xlab='Speed (km/h)',ylab='Power (kW)',h=280),
        use_container_width=True)

    # Cd sensitivity on this tab
    c1,c2=st.columns(2)
    with c1:
        st.plotly_chart(pline(
            [d['cd'] for d in R['cd_sens']],
            {'Range (km)':[d['range'] for d in R['cd_sens']],
             f'Target ({range_km} km)':[range_km for _ in R['cd_sens']]},
            title='Cd → Achievable Range',xlab='Drag Coefficient Cd',ylab='Range (km)',h=270),
        use_container_width=True)
    with c2:
        st.plotly_chart(pline(
            [d['cd'] for d in R['cd_sens']],
            {'Motor Req (kW)':[d['motor_kw'] for d in R['cd_sens']],
             f'Motor Cont ({motor_cont} kW)':[motor_cont for _ in R['cd_sens']]},
            title='Cd → Motor Power Required at Grade',xlab='Drag Coefficient Cd',ylab='kW',h=270),
        use_container_width=True)

# ────────────────────────────────────────────────────────────────────────
# TAB 3 — BATTERY
# ────────────────────────────────────────────────────────────────────────
if active_section == "Battery":
    c1,c2=st.columns(2)
    with c1:
        st.subheader("Energy Sizing")
        bkpis=[("Physics E_design",f"{R['E_design']*1000:.1f}","Wh/km (from road load)"),
               ("Manual E_design",f"{R['E_gross_duty_manual']*rw_margin*1000:.1f}","Wh/km (reference)"),
               ("Mission Energy",f"{R['E_mission']:.1f}","kWh"),
               ("Total Reserves",f"{R['E_reserves']:.2f}","kWh"),
               ("Usable Needed",f"{R['E_usable']:.1f}","kWh"),
               ("SoC Window",f"{R['socWindow']*100:.1f}","%"),
               ("Gross Pack Req",f"{R['E_gross']:.1f}","kWh"),
               ("Regen Recovery",f"{R['E_regen_net']/R['E_gross_duty']*100:.1f}","% of gross")]
        ecols=st.columns(4)
        for i,(l,v,u) in enumerate(bkpis):
            ecols[i%4].markdown(mc(l,v,u,'g' if i==6 and R['E_pack']>=R['E_gross'] else ''),unsafe_allow_html=True)

        st.markdown(f"""
| Step | Formula | Value |
|---|---|---|
| Physics Urban | F_urban/(η×3600) + stop-go | **{R['eng_phys_urban']*1000:.2f} Wh/km** |
| Physics Transit | F_transit/(η×3600) + stop-go | **{R['eng_phys_transit']*1000:.2f} Wh/km** |
| Physics Highway | F_highway/(η×3600) | **{R['eng_phys_highway']*1000:.2f} Wh/km** |
| Weighted gross duty | Σ frac_i × e_i | **{R['E_gross_duty']*1000:.2f} Wh/km** |
| Regen net | 0.30 × (urban+transit contrib) × η_regen | **{R['E_regen_net']*1000:.2f} Wh/km** |
| Design target | (gross − regen) × {rw_margin} | **{R['E_design']*1000:.2f} Wh/km** |
| Mission | {range_km} km × {R['E_design']*1000:.2f} Wh/km | **{R['E_mission']:.1f} kWh** |
| **Usable needed** | mission + reserves | **{R['E_usable']:.1f} kWh** |
| **Gross pack req** | {R['E_usable']:.1f} / {R['socWindow']*100:.1f}% | **{R['E_gross']:.1f} kWh** |
""")

    with c2:
        st.subheader("Pack Configuration")
        pcols=st.columns(4)
        pkpis=[("Config",f"{series_cells}S{parallel_str}P",f"{series_cells*parallel_str} cells"),
               ("V nominal",f"{R['V_pack_nom']:.0f}","V"),
               ("Pack Ah",f"{R['packAh']}","Ah"),
               ("Gross Pack",f"{R['E_pack']:.1f}","kWh"),
               ("Cruise C",f"{R['C_cruise']:.2f}","C"),("Peak C",f"{R['C_peak']:.2f}","C"),
               ("DCFC C",f"{R['C_dcfc']:.2f}","C"),("AC C",f"{R['C_ac']:.2f}","C")]
        for i,(l,v,u) in enumerate(pkpis):
            col='g' if (i==3 and R['E_pack']>=R['E_gross']) else ''
            pcols[i%4].markdown(mc(l,v,u,col),unsafe_allow_html=True)

        st.markdown(f"""
| Condition | I (A) | C-rate | Limit | Status |
|---|---|---|---|---|
| Cruise | {R['I_cruise']:.0f} | {R['C_cruise']:.2f} C | 3 C | {"✅" if R['C_cruise']<3 else "❌"} |
| Peak 30s | {R['I_peak_A']:.0f} | {R['C_peak']:.2f} C | 5 C | {"✅" if R['C_peak']<5 else "❌"} |
| DCFC | {R['I_dcfc']:.0f} | {R['C_dcfc']:.2f} C | 1.5 C | {"✅" if R['C_dcfc']<1.5 else "❌"} |
| AC charge | {R['I_ac']:.0f} | {R['C_ac']:.2f} C | 0.5 C | {"✅" if R['C_ac']<0.5 else "⚠"} |
""")

    c1,c2=st.columns(2)
    with c1:
        bot_g=round(I['botGuard']*100,1); top_g=round(I['topGuard']*100,1); usable_w=round(R['socWindow']*100,1)
        fig_soc = go.Figure(data=[
    go.Bar(name='Bottom Guard', y=['SoC'], x=[bot_g], orientation='h',
           marker_color=hex_to_rgba(RED, 0.53)),
    go.Bar(name='Usable SoC', y=['SoC'], x=[usable_w], orientation='h',
           marker_color=hex_to_rgba(GREEN, 0.73)),
    go.Bar(name='Top Guard', y=['SoC'], x=[top_g], orientation='h',
           marker_color=hex_to_rgba(AMBER, 0.53)),
        ])
        fig_soc.update_layout(barmode='stack',title='SoC Window',height=160,
                              margin=dict(l=8,r=8,t=30,b=8),plot_bgcolor='white',paper_bgcolor='white',
                              xaxis=dict(range=[0,100],title='SoC (%)',gridcolor='#F1F5F9'),font_size=11)
        st.plotly_chart(fig_soc,use_container_width=True)
    with c2:
        st.plotly_chart(pbar(
            ['Mission','+Fan','+Route','+DCIR','+Buf','Usable','Gross Req','Pack Config'],
            [round(R['E_mission'],1),round(R['res_fan'],2),round(R['res_route'],2),
             round(R['res_dcir'],2),round(R['res_buf'],2),round(R['E_usable'],1),round(R['E_gross'],1),round(R['E_pack'],1)],
            colors=[BLUE,AMBER,AMBER,AMBER,AMBER,GREEN,RED,'#34D399'],
            title='Energy Waterfall (kWh)',ylab='kWh',h=240),use_container_width=True)

# ────────────────────────────────────────────────────────────────────────
# TAB 4 — MOTOR & DRIVE
# ────────────────────────────────────────────────────────────────────────
if active_section == "Drive":
    motor_pass=R['motor_cont_ok'] and R['motor_peak_ok'] and R['motor_speed_ok'] and R['torque_ok']
    bc2=GREEN if motor_pass else RED
    bt2="✅ Motor Passes All Checks" if motor_pass else "❌ Motor Does Not Meet Requirements"
    st.markdown(f'<div style="background:{bc2}18;border:2px solid {bc2};border-radius:10px;padding:12px 16px;margin-bottom:12px;font-size:13px;font-weight:700;color:{bc2};">{bt2}</div>',unsafe_allow_html=True)

    c1,c2=st.columns(2)
    with c1:
        st.markdown("**Requirements (from GVW, Grade, Speed, Cd, Tyres)**")
        rmkpis=[
            ("P_wheel at grade",  f"{kw(R['P_wheel_grade']):.2f}", "kW  ← design load"),
            ("P motor req cont",  f"{kw(R['P_req_design_W']):.2f}", "kW (+10% margin)"),
            ("P motor req peak",  f"{kw(R['P_req_peak_W']):.2f}",  "kW (accel check)"),
            ("T_req at wheel",    f"{R['T_req_grade_Nm']:.0f}",    "Nm (from r_dyn×F)"),
            ("T_avail at wheel",  f"{R['T_wheel_peak']:.0f}",      "Nm"),
            ("Torque margin",     f"{R['torque_margin']:.1f}",     f"% {'✅' if R['torque_ok'] else '❌'}"),
            ("FW power margin",   f"{R['fw_margin']:.1f}",         "% (flat top speed)"),
            ("Accel rate",        f"{R['a_accel']:.2f}",           f"m/s² (0→60 in {accel_time}s)"),
        ]
        rcols=st.columns(2)
        for i,(l,v,u) in enumerate(rmkpis):
            c='g' if ('✅' in u or (i==5 and R['torque_ok'])) else ('r' if '❌' in u else '')
            rcols[i%2].markdown(mc(l,v,u,c),unsafe_allow_html=True)

        st.markdown(f"""
| Step | Formula | Result |
|---|---|---|
| η chain | {motor_eff} × {gear_eff} | **{motor_eff*gear_eff:.3f}** |
| P_wheel grade | {R['F_total_grade']:.0f} N × {grade_speed/3.6:.2f} m/s | **{kw(R['P_wheel_grade']):.2f} kW** |
| P motor cont | {kw(R['P_wheel_grade']):.2f} / {motor_eff*gear_eff:.3f} | **{kw(R['P_req_cont_W']):.2f} kW** |
| +10% margin | {kw(R['P_req_cont_W']):.2f} × 1.10 | **{kw(R['P_req_design_W']):.2f} kW** |
| T_req (wheel) | F_grade×r_dyn = {R['F_total_grade']:.0f}×{R['r_dyn']:.3f} | **{R['T_req_grade_Nm']:.0f} Nm** |
| T_shaft peak | P_peak×60/(2π×{motor_base_rpm}) | **{R['T_user_peak']:.0f} Nm** |
| T_wheel avail | {R['T_user_peak']:.0f}×{R['gearRatio']:.2f}×{gear_eff} | **{R['T_wheel_peak']:.0f} Nm** |
| **Torque margin** | (avail−req)/req | **{R['torque_margin']:.1f}%** |
""")

    with c2:
        st.markdown("**Gear & Speed Chain**")
        gkpis=[
            ("Tyre r_dyn",        f"{R['r_dyn']*1000:.0f}",    "mm"),
            ("N_wheel at top spd",f"{R['N_wheel']:.0f}",        "rpm"),
            ("Gear Ratio i",      f"{R['gearRatio']:.2f}",      ":1"),
            ("Motor rpm at top",  f"{R['N_motor_at_top']:.0f}", f"rpm {'✅' if R['motor_speed_ok'] else '❌'}"),
        ]
        for l,v,u in gkpis:
            c='g' if '✅' in u else ('r' if '❌' in u else '')
            st.markdown(mc(l,v,u,c),unsafe_allow_html=True)

        # Tyre sensitivity
        st.markdown("**Tyre Size → Gear Ratio & Torque Req**")
        st.plotly_chart(go.Figure(data=[
            go.Scatter(x=[d['r_dyn_mm'] for d in R['tyre_sens']],
                       y=[d['T_req_Nm'] for d in R['tyre_sens']],
                       name='Wheel Torque Req (Nm)',line=dict(color=BLUE,width=2)),
        ]).update_layout(title='Tyre r_dyn → Torque Requirement',height=200,
                         xaxis_title='Dynamic radius (mm)',yaxis_title='Torque (Nm)',**LAYOUT),
        use_container_width=True)
        st.plotly_chart(go.Figure(data=[
            go.Scatter(x=[d['r_dyn_mm'] for d in R['tyre_sens']],
                       y=[d['gear_ratio_auto'] for d in R['tyre_sens']],
                       name='Auto Gear Ratio',line=dict(color=AMBER,width=2)),
        ]).update_layout(title='Tyre r_dyn → Required Gear Ratio (Auto Mode)',height=180,
                         xaxis_title='Dynamic radius (mm)',yaxis_title='Gear Ratio :1',**LAYOUT),
        use_container_width=True)

    st.markdown("---")
    c1,c2=st.columns(2)
    with c1:
        # Torque-speed curve
        rpms,Tpeak,Tcont,Ppeak=[],[],[],[]
        for N in range(0, motor_max_rpm+501, 250):
            rpms.append(N)
            Tp=R['T_user_peak'] if N<=motor_base_rpm else R['P_user_peak']*60/(2*math.pi*max(N,1))
            Tc=R['T_user_cont'] if N<=motor_base_rpm else R['P_user_cont']*60/(2*math.pi*max(N,1))
            Tpeak.append(max(0,round(Tp))); Tcont.append(max(0,round(Tc)))
            Ppeak.append(round(min(R['P_user_peak'],R['T_user_peak']*2*math.pi*N/60)/1000,1) if N>0 else 0)
        fig_tq=go.Figure()
        fig_tq.add_trace(go.Scatter(x=rpms,y=Tpeak,name='Peak Torque (Nm)',line=dict(color=BLUE,width=2),yaxis='y1'))
        fig_tq.add_trace(go.Scatter(x=rpms,y=Tcont,name='Cont Torque (Nm)',line=dict(color=GREEN,dash='dash',width=2),yaxis='y1'))
        fig_tq.add_trace(go.Scatter(x=rpms,y=Ppeak,name='Peak Power (kW)',line=dict(color=AMBER,width=2),yaxis='y2'))
        # Add required torque at wheel (back-calculated to motor shaft)
        T_req_shaft = R['T_req_grade_Nm'] / (R['gearRatio'] * gear_eff)
        fig_tq.add_hline(y=T_req_shaft,line=dict(color=RED,dash='dot',width=1.5),
                          annotation_text=f"Req shaft {T_req_shaft:.0f} Nm",annotation_position="top right",yref='y1')
        fig_tq.update_layout(title='Torque–Speed Curve',height=290,
                              margin=dict(l=8,r=55,t=32,b=8),plot_bgcolor='white',paper_bgcolor='white',
                              xaxis=dict(title='Motor rpm',gridcolor='#F1F5F9'),
                              yaxis=dict(title='Torque (Nm)',gridcolor='#F1F5F9'),
                              yaxis2=dict(title='Power (kW)',overlaying='y',side='right',gridcolor='rgba(0,0,0,0)'),
                              font_size=11,legend_font_size=10)
        st.plotly_chart(fig_tq,use_container_width=True)
    with c2:
        st.plotly_chart(pline(
            [d['ratio'] for d in R['gear_sens']],
            {'Wheel Torque (Nm)':[d['wheelTorque'] for d in R['gear_sens']],
             f'Required ({R["T_req_grade_Nm"]:.0f} Nm)':[round(R['T_req_grade_Nm']) for _ in R['gear_sens']]},
            title='Gear Ratio vs Wheel Torque',xlab='Gear Ratio :1',ylab='Nm',h=290),
        use_container_width=True)

# ────────────────────────────────────────────────────────────────────────
# TAB 5 — CHARGING
# ────────────────────────────────────────────────────────────────────────
if active_section == "Charging":
    chg_kpis=[("AC Charge",f"{R['t_ac_h']:.1f}","h (0→100%)"),
              ("DC Fast Charge",f"{R['t_dc_min']:.0f}","min (20→80%)"),
              ("V2L Duration",f"{R['t_v2l_h']:.1f}","h at 16A"),
              ("AC C-rate",f"{R['C_ac']:.2f}","C"),
              ("DCFC C-rate",f"{R['C_dcfc']:.2f}","C"),
              ("DCFC Vsag",f"{R['V_sag_dcfc']:.1f}",f"V ({R['V_sag_pct_dcfc']:.1f}%)")]
    cols=st.columns(6)
    for i,(l,v,u) in enumerate(chg_kpis): cols[i].markdown(mc(l,v,u),unsafe_allow_html=True)

    if R['dcfc_derate_flag']:
        st.markdown(f'<div class="warnbox">⚠ <b>DCFC Voltage Sag Warning:</b> Pack DCIR {pack_dcir_mo} mΩ causes {R["V_sag_dcfc"]:.1f} V sag ({R["V_sag_pct_dcfc"]:.1f}%) during DCFC. Charger may derate. Consider reducing DCIR or pack current.</div>', unsafe_allow_html=True)

    c1,c2,c3=st.columns(3)
    P_derate_45=dcfc_power-2.5*(ambient-40)
    t_derate=(R['E_dcfc_ch']/(max(1,P_derate_45)*dcfc_eff)*60) if ambient>40 else None
    with c1:
        st.markdown("**AC Charging (Type-2 OBC)**")
        st.markdown(f"""
| Parameter | Value |
|---|---|
| OBC Power | {obc_power} kW |
| OBC η | {obc_eff*100:.1f}% |
| Pack current | {R['I_ac']:.1f} A |
| Cell current (÷{parallel_str}P) | {R['I_ac']/parallel_str:.1f} A = {R['C_ac']:.2f} C |
| **Full charge (0→100%)** | **{R['t_ac_h']:.1f} h** |
| Thermal impact | {"✅ <0.5C" if R['C_ac']<0.5 else "⚠ Check"} |
""")
    with c2:
        st.markdown("**DC Fast Charging (CCS2)**")
        derate_row=f"| Derated at {ambient}°C | {P_derate_45:.1f} kW → {t_derate:.0f} min |" if ambient>40 else ""
        st.markdown(f"""
| Parameter | Value |
|---|---|
| DCFC Power | {dcfc_power} kW |
| Charge window | 20%→80% = {R['E_dcfc_ch']:.1f} kWh |
| Pack current | {R['I_dcfc']:.1f} A ({R['C_dcfc']:.2f} C) |
| **Charge time (20→80%)** | **{R['t_dc_min']:.0f} min** |
| Vsag at DCFC current | {R['V_sag_dcfc']:.1f} V ({R['V_sag_pct_dcfc']:.1f}%) |
{derate_row}
""")
    with c3:
        st.markdown("**V2L Export**")
        st.markdown(f"""
| Parameter | Value |
|---|---|
| V2L Output | 230V / 16A |
| Power | {R['P_v2l']/1000:.2f} kW |
| HV Draw | {R['P_v2l_draw']/1000:.1f} kW |
| Max Duration | {R['t_v2l_h']:.1f} h |
""")

    st.plotly_chart(pbar(
        [f"AC Full Charge\n(Type-2 {obc_power}kW)",f"DC 20→80%\n(CCS2 {dcfc_power}kW)","V2L to 20% SoC\n(230V 16A)"],
        [round(R['t_ac_h']*60),round(R['t_dc_min']),round(R['t_v2l_h']*60)],
        colors=[BLUE,'#64B5F6',GREEN],title='Charging Time (minutes)',ylab='Minutes',h=260),
    use_container_width=True)

# ────────────────────────────────────────────────────────────────────────
# TAB 6 — THERMAL
# ────────────────────────────────────────────────────────────────────────
if active_section == "Thermal":
    st.markdown(f'<div class="infobox">⚙ <b>DCIR Coupling Active:</b> Pack DCIR = {pack_dcir_mo} mΩ → V_sag at peak = {R["V_sag_peak"]:.1f} V | Power derating = {R["P_derate_pct"]:.1f}% | Heat at peak = {R["Q_peak_W"]:.0f} W</div>', unsafe_allow_html=True)

    c1,c2=st.columns(2)
    with c1:
        st.markdown("**Battery Thermal (DCIR coupled)**")
        st.markdown(f"""
| Condition | I (A) | V_sag (V) | Heat (W) | Air Cool (W) | Status |
|---|---|---|---|---|---|
| DCFC | {R['I_dcfc']:.0f} | {R['V_sag_dcfc']:.1f} | {R['Q_dcfc_W']:.0f} | {R['Q_air_W']:.0f} | {"✅" if R['Q_dcfc_W']<R['Q_air_W'] else "⚠ PCM"} |
| Cruise | {R['I_cruise']:.0f} | {R['V_sag_cruise']:.1f} | {R['Q_cruise_W']:.0f} | {R['Q_air_W']:.0f} | {"✅" if R['Q_cruise_W']<R['Q_air_W'] else "⚠ PCM"} |
| **Peak 30s** | **{R['I_peak_A']:.0f}** | **{R['V_sag_peak']:.1f}** | **{R['Q_peak_W']:.0f}** | **{R['Q_air_W']:.0f}** | **{R['Q_net_pcm']:.0f} W net** |
""")
        st.markdown(f"""
| PCM Sizing (RT42) | Value |
|---|---|
| Net heat to PCM | {R['Q_net_pcm']:.0f} W |
| 10 events × 30s | {R['Q_net_pcm']*300/1000:.1f} kJ |
| PCM mass (latent) | {R['m_pcm_min']:.2f} kg |
| Corrected design | {R['m_pcm_corr']:.2f} kg → **8 kg RT42** |
""")
    with c2:
        st.markdown("**Motor Thermal**")
        st.markdown(f"""
| Parameter | Value |
|---|---|
| Continuous heat | {R['Q_motor_cont_W']:.0f} W |
| Peak heat (30s) | {R['Q_motor_peak_W']:.0f} W |
| Winding temp (est.) | {R['T_winding']:.0f} °C |
| Class F limit | 155 °C |
| **Thermal headroom** | **{155-R['T_winding']:.0f} °C** {"✅" if R['T_winding']<130 else "⚠"} |
""")
        # DCIR sweep chart
        st.plotly_chart(pline(
            [d['dcir'] for d in R['dcir_sens']],
            {'Heat at Peak (W)':[d['heat_w'] for d in R['dcir_sens']],
             'Air Cooling Cap (W)':[round(R['Q_air_W']) for _ in R['dcir_sens']]},
            title='Pack DCIR → Heat at Peak 30s',xlab='DCIR (mΩ)',ylab='Watts',h=220),
        use_container_width=True)

    c1,c2=st.columns(2)
    with c1:
        fig_th=go.Figure(data=[
            go.Bar(name='Heat Gen (W)',x=['DCFC','Cruise','Peak 30s'],
                   y=[R['Q_dcfc_W'],R['Q_cruise_W'],R['Q_peak_W']],marker_color=[AMBER,BLUE,RED]),
            go.Bar(name='Air Cooling (W)',x=['DCFC','Cruise','Peak 30s'],
                   y=[R['Q_air_W']]*3,marker_color=['rgba(16,185,129,0.6)']*3),
        ])
        fig_th.update_layout(title='Heat Generation vs Air Cooling',barmode='group',height=260,**LAYOUT,yaxis_title='Watts')
        st.plotly_chart(fig_th,use_container_width=True)
    with c2:
        st.plotly_chart(pline(
            [d['dcir'] for d in R['dcir_sens']],
            {'V_sag at Peak (V)':[d['vsag'] for d in R['dcir_sens']],
             'Actual Power (kW)':[d['power_kw'] for d in R['dcir_sens']]},
            title='DCIR → Voltage Sag & Available Power',xlab='DCIR (mΩ)',ylab='V / kW',h=260),
        use_container_width=True)

# ────────────────────────────────────────────────────────────────────────
# TAB 7 — BRAKING & SAFETY
# ────────────────────────────────────────────────────────────────────────
if active_section == "Safety":
    c1,c2=st.columns(2)
    with c1:
        st.markdown("**Braking System**")
        st.markdown(f"""
| Parameter | Formula | Value |
|---|---|---|
| Required decel | v²/(2×50) = ({top_speed/3.6:.1f})²/100 | **{R['a_req']:.2f} m/s² = {R['mu_eq']:.2f}g** |
| Total brake force | {gvw}×{R['a_req']:.2f} | **{R['F_brake_total']:.0f} N** |
| Max regen @ 60 km/h | 30 kW / 16.7 m/s | **{R['F_regen_brk']:.0f} N** |
| Friction brake | {R['F_brake_total']:.0f}−{R['F_regen_brk']:.0f} | **{R['F_friction_brk']:.0f} N** |
| **Regen contribution** | | **{R['F_regen_brk']/R['F_brake_total']*100:.1f}%** |
| Front (60% split) | | {R['F_friction_brk']*0.6:.0f} N |
| Rear (40% split) | | {R['F_friction_brk']*0.4:.0f} N |
""")
    with c2:
        st.markdown("**HV Protection**")
        fuse_rating=math.ceil(motor_peak*1000/R['V_pack_nom']/50)*50
        st.markdown(f"""
| Element | Specification |
|---|---|
| Pack max voltage | {R['V_pack_max']:.1f} V |
| Bolted fault current | {R['I_fault']:.0f} A |
| **Fuse rating** | **{fuse_rating} A / {R['V_pack_max']+135:.0f} V DC** |
| Precharge resistor | {R['R_precharge']:.0f} Ω |
| IMD trip threshold | {R['R_iso_trip']/1000:.0f} kΩ |
""")
    st.markdown("**LV Architecture**")
    c1,c2=st.columns([1,2])
    with c1:
        for l,v,u in [("DC-DC","3","kW"),("LV Bus","13.8","V"),("LV Load",str(R['LV_load']),"W"),("AGM Rsv",f"{R['t_agm_h']:.1f}","h")]:
            st.markdown(mc(l,v,u),unsafe_allow_html=True)
    with c2:
        lv_loads=[("BMS",25),("VCU",20),("ADAS cameras",60),("Telematics",15),
                  ("Battery fan",50),("Motor fan",50),("LED lighting",80),("EPS",300),("HVAC",80),("Misc",50)]
        st.markdown("| Load | W |\n|---|---|\n"+"".join(f"| {l} | {w} |\n" for l,w in lv_loads)+f"| **Total** | **730** |")

# ────────────────────────────────────────────────────────────────────────
# TAB 8 — CHASSIS
# ────────────────────────────────────────────────────────────────────────
if active_section == "Chassis":
    c1,c2=st.columns(2)
    with c1:
        st.markdown("**Suspension Loads (COUPLED to GVW)**")
        st.markdown(f"""
| Parameter | Value |
|---|---|
| Front axle (55%) | {R['F_front']:.0f} N |
| Rear axle (45%) | {R['F_rear']:.0f} N |
| Per front spring | {R['F_front']/2:.0f} N |
| Per rear spring | {R['F_rear']/2:.0f} N |
| Front spring rate | {R['k_front']/1000:.0f} kN/m sys → {R['k_front']/2000:.0f} kN/m each |
| Rear spring rate | {R['k_rear']/1000:.0f} kN/m sys → {R['k_rear']/2000:.0f} kN/m each |
""")
    with c2:
        st.markdown("**Ride & Steering**")
        st.markdown("""
| Parameter | Value |
|---|---|
| Front ride freq | 1.20 Hz |
| Rear ride freq | 1.35 Hz |
| Bump travel target | ≥ 150 mm |
| Turning circle | ≤ 10.5 m |
| EPS assist ratio | 12:1 |
""")
    st.plotly_chart(pbar(['Front Axle','Rear Axle'],[round(R['F_front']),round(R['F_rear'])],
                          colors=[BLUE,GREEN],title='Axle Load Distribution',ylab='Force (N)',h=240),
    use_container_width=True)

# ────────────────────────────────────────────────────────────────────────
# TAB 9 — SENSITIVITY (all physics-coupled)
# ────────────────────────────────────────────────────────────────────────
if active_section == "Sensitivity":
    st.markdown('<div class="infobox">📊 All curves derived from physics model — changing GVW, Cd, grade, etc. in the sidebar updates every chart here automatically.</div>', unsafe_allow_html=True)

    # Row 1: GVW & Payload
    c1,c2=st.columns(2)
    with c1:
        st.plotly_chart(pline(
            [d['gvw'] for d in R['gvw_sens']],
            {'Range (km)':[d['range'] for d in R['gvw_sens']],
             f'Target ({range_km} km)':[range_km for _ in R['gvw_sens']]},
            title='GVW → Achievable Range (physics)',xlab='GVW (kg)',ylab='Range (km)',h=270),
        use_container_width=True)
    with c2:
        st.plotly_chart(pline(
            [d['gvw'] for d in R['gvw_sens']],
            {'Motor Req (kW)':[d['motor_req_kw'] for d in R['gvw_sens']],
             f'Motor Cont ({motor_cont} kW)':[motor_cont for _ in R['gvw_sens']]},
            title='GVW → Motor Power Required at Grade',xlab='GVW (kg)',ylab='kW',h=270),
        use_container_width=True)

    # Row 2: Payload & Ambient
    c1,c2=st.columns(2)
    with c1:
        st.plotly_chart(pline(
            [d['payload'] for d in R['payload_sens']],
            {'Range (km)':[d['range'] for d in R['payload_sens']],
             f'Target ({range_km} km)':[range_km for _ in R['payload_sens']]},
            title='Payload → Range (physics)',xlab='Payload (kg)',ylab='Range (km)',h=270),
        use_container_width=True)
    with c2:
        st.plotly_chart(pline(
            [d['temp'] for d in R['ambient_sens']],
            {'Range (km)':[d['range'] for d in R['ambient_sens']],
             f'Target ({range_km} km)':[range_km for _ in R['ambient_sens']]},
            title='Ambient Temp → Range',xlab='Ambient (°C)',ylab='Range (km)',h=270),
        use_container_width=True)

    # Row 3: Grade & Grade speed
    c1,c2=st.columns(2)
    with c1:
        glab=[f"{d['grade']}%" for d in R['grade_sens']]
        gpwr=[d['motorPowerKW'] for d in R['grade_sens']]
        gcol=[GREEN if d['canClimb'] else RED for d in R['grade_sens']]
        fig_gr=go.Figure()
        fig_gr.add_trace(go.Bar(x=glab,y=gpwr,marker_color=gcol,name='Motor Power Req (kW)',
                                 text=[f"{p}" for p in gpwr],textposition='outside'))
        fig_gr.add_trace(go.Scatter(x=glab,y=[motor_cont]*len(glab),mode='lines',
                                     name=f'Motor Cont ({motor_cont} kW)',
                                     line=dict(color=GREEN,dash='dash',width=2)))
        fig_gr.update_layout(title='Grade → Motor Power Required',height=270,
                              yaxis_title='kW',**LAYOUT)
        st.plotly_chart(fig_gr,use_container_width=True)
    with c2:
        st.plotly_chart(pline(
            [d['speed'] for d in R['grade_speed_sens']],
            {'Motor kW':[d['motorKW'] for d in R['grade_speed_sens']],
             f'Motor Cont ({motor_cont} kW)':[motor_cont for _ in R['grade_speed_sens']]},
            title=f'Grade Climbing Speed → Motor Power ({grade}% grade)',
            xlab='Climbing Speed (km/h)',ylab='kW',h=270),
        use_container_width=True)

    # Row 4: Cd & Wheel torque at grade
    c1,c2=st.columns(2)
    with c1:
        st.plotly_chart(pline(
            [d['cd'] for d in R['cd_sens']],
            {'Range (km)':[d['range'] for d in R['cd_sens']],
             'Motor Req (kW)':[d['motor_kw'] for d in R['cd_sens']]},
            title='Drag Coefficient → Range & Motor',xlab='Cd',ylab='km / kW',h=270),
        use_container_width=True)
    with c2:
        # Wheel torque at grade for each grade value
        st.plotly_chart(pline(
            [f"{d['grade']}%" for d in R['grade_sens']],
            {'Wheel Torque Req (Nm)':[d['wheelTorqueNm'] for d in R['grade_sens']],
             f'Wheel Torque Avail ({R["T_wheel_peak"]:.0f} Nm)':[round(R['T_wheel_peak']) for _ in R['grade_sens']]},
            title='Grade → Wheel Torque Required vs Available',xlab='Grade',ylab='Nm',h=270),
        use_container_width=True)


# ------------------------------------------------------------------------
# TAB 10 - ENGINEER WORKBENCH
# ------------------------------------------------------------------------
if active_section == "Engineer":
    st.markdown('<div class="infobox">Engineer workbench: calibration visibility, sensitivity leverage, and actionable design closures.</div>', unsafe_allow_html=True)

    c1,c2,c3,c4=st.columns(4)
    c1.markdown(mc('Design Energy',f"{R['E_design']*1000:.1f}",'Wh/km','a' if R['real_world_factor']>1.15 else 'g'),unsafe_allow_html=True)
    c2.markdown(mc('Regen Capture',f"{R['regen_capture']*100:.0f}",'% of U+T braking'),unsafe_allow_html=True)
    c3.markdown(mc('Aux Load',f"{R['aux_kw']:.1f}",'kW continuous'),unsafe_allow_html=True)
    c4.markdown(mc('RW Factor',f"x{R['real_world_factor']:.2f}",'sizing multiplier','a' if R['real_world_factor']>1.20 else ''),unsafe_allow_html=True)

    gvw_span=max(1,R['gvw_sens'][-1]['gvw']-R['gvw_sens'][0]['gvw'])
    payload_span=max(1,R['payload_sens'][-1]['payload']-R['payload_sens'][0]['payload'])
    cd_span=max(0.01,R['cd_sens'][-1]['cd']-R['cd_sens'][0]['cd'])

    gvw_lever=(R['gvw_sens'][0]['range']-R['gvw_sens'][-1]['range'])/(gvw_span/100)
    payload_lever=(R['payload_sens'][0]['range']-R['payload_sens'][-1]['range'])/(payload_span/100)
    cd_lever=(R['cd_sens'][0]['range']-R['cd_sens'][-1]['range'])/cd_span

    st.markdown('**Primary Levers (from current sensitivity runs)**')
    st.markdown(
        '| Lever | Observed impact | Suggested engineering action |\n'
        '|---|---|---|\n'
        f"| Vehicle mass | {gvw_lever:.2f} km per +100 kg | Prioritize mass-out in body/chassis and tire rolling losses |\n"
        f"| Payload effect | {payload_lever:.2f} km per +100 kg | Tune duty assumptions and payload derating strategy |\n"
        f"| Aerodynamics | {cd_lever:.1f} km per +1.0 Cd | Improve front profile, mirrors, underbody, and grille sealing |\n"
    )

    eng_actions=[]
    if not R['motor_cont_ok']:
        eng_actions.append('Increase continuous motor rating or lower grade-speed target.')
    if not R['motor_peak_ok']:
        eng_actions.append('Increase peak motor capability or relax 0-60 target.')
    if not R['torque_ok']:
        eng_actions.append('Increase gear ratio or shaft torque to recover wheel torque margin.')
    if R['pack_margin_pct'] < 8:
        eng_actions.append('Increase gross pack capacity or reduce design Wh/km by aero/mass improvements.')
    if R['C_dcfc'] > 1.5:
        eng_actions.append('Reduce DCFC current per parallel path or increase parallel strings.')

    if eng_actions:
        st.markdown('**Engineering Closure List**')
        for i, action in enumerate(eng_actions, 1):
            st.markdown(f"{i}. {action}")
    else:
        st.markdown('<div class="rolebox">All primary engineering gates are currently on-track for this input set.</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------
# TAB 11 - END CUSTOMER VIEW
# ------------------------------------------------------------------------
if active_section == "Customer":
    st.markdown('<div class="infobox">Customer view: practical range expectations, running cost, and charging convenience.</div>', unsafe_allow_html=True)

    daily_km = st.number_input('Daily driving distance (km)', value=80, min_value=10, max_value=400, step=5)
    tariff = st.number_input('Electricity tariff (INR/kWh)', value=10.0, min_value=2.0, max_value=40.0, step=0.5)
    diesel_price = st.number_input('Diesel price (INR/L)', value=95.0, min_value=50.0, max_value=200.0, step=1.0)
    diesel_kmpl = st.number_input('Comparable diesel efficiency (km/L)', value=10.0, min_value=4.0, max_value=25.0, step=0.5)

    payload_sorted=sorted(R['payload_sens'], key=lambda d:d['payload'])
    no_load_est=payload_sorted[0]['range']
    full_load_est=payload_sorted[-1]['range']

    c1,c2,c3,c4=st.columns(4)
    c1.markdown(mc('Expected Range (light load)',f"{no_load_est}",'km','g'),unsafe_allow_html=True)
    c2.markdown(mc('Expected Range (full payload)',f"{full_load_est}",'km','a'),unsafe_allow_html=True)
    c3.markdown(mc('Energy Use',f"{R['E_design']*1000:.1f}",'Wh/km'),unsafe_allow_html=True)
    c4.markdown(mc('AC Full Charge',f"{R['t_ac_h']:.1f}",'hours'),unsafe_allow_html=True)

    ev_cost_per_km = R['E_design'] * tariff
    diesel_cost_per_km = diesel_price / max(0.1, diesel_kmpl)
    monthly_km = daily_km * 30
    monthly_ev = ev_cost_per_km * monthly_km
    monthly_diesel = diesel_cost_per_km * monthly_km
    monthly_saving = monthly_diesel - monthly_ev

    st.markdown(
        '| Metric | Value |\n'
        '|---|---|\n'
        f"| EV running cost | INR {ev_cost_per_km:.2f}/km |\n"
        f"| Diesel running cost | INR {diesel_cost_per_km:.2f}/km |\n"
        f"| Monthly EV energy cost ({monthly_km:.0f} km) | INR {monthly_ev:,.0f} |\n"
        f"| Monthly diesel fuel cost ({monthly_km:.0f} km) | INR {monthly_diesel:,.0f} |\n"
        f"| Monthly saving with EV | INR {monthly_saving:,.0f} |\n"
    )

    usable_trip_range = max(1, R['range_actual'] * 0.80)
    charges_per_week = (daily_km * 7) / usable_trip_range
    trip_km = st.number_input('Intercity trip distance (km)', value=320, min_value=50, max_value=2000, step=10)
    dc_hop_range = max(1, R['range_actual'] * 0.65)
    dc_stops = max(0, math.ceil(max(0, trip_km - R['range_actual']) / dc_hop_range))

    st.markdown('<div class="rolebox">'
                f"Weekly charging estimate: ~{charges_per_week:.1f} equivalent full charges/week for {daily_km} km/day.<br>"
                f"For a {trip_km} km trip, plan approximately {dc_stops} DC fast-charge stop(s)."
                '</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------
# TAB 12 - PROJECT MANAGER DASHBOARD
# ------------------------------------------------------------------------
if active_section == "PM":
    st.markdown('<div class="infobox">PM dashboard: gate status, risks, and launch-readiness summary.</div>', unsafe_allow_html=True)

    gates=[
        ('Range target', R['range_actual']>=range_km, f"{R['range_actual']:.0f}/{range_km} km"),
        ('Motor continuous', R['motor_cont_ok'], f"Need {kw(R['P_req_design_W']):.1f} vs {kw(R['P_user_cont']):.1f} kW"),
        ('Motor peak', R['motor_peak_ok'], f"Need {kw(R['P_req_peak_W']):.1f} vs {kw(R['P_user_peak']):.1f} kW"),
        ('Torque margin', R['torque_margin']>0, f"{R['torque_margin']:.1f}%"),
        ('Pack adequacy', R['E_pack']>=R['E_gross'], f"{R['pack_margin_pct']:+.1f}%"),
        ('Charging KPI', R['t_dc_min']<60, f"{R['t_dc_min']:.0f} min DCFC"),
        ('Thermal KPI', R['T_winding']<155, f"{R['T_winding']:.0f}C winding"),
    ]

    passed=sum(1 for _,ok,_ in gates if ok)
    gate_score=passed/len(gates)*100

    c1,c2=st.columns([1,2])
    with c1:
        fig_pm=go.Figure(go.Indicator(
            mode='gauge+number',
            value=gate_score,
            gauge={
                'axis':{'range':[0,100]},
                'bar':{'color':GREEN if gate_score>=85 else (AMBER if gate_score>=70 else RED)},
                'steps':[{'range':[0,70],'color':'#FEE2E2'},{'range':[70,85],'color':'#FEF3C7'},{'range':[85,100],'color':'#ECFDF5'}],
            },
            title={'text':'Gate Pass %'}
        ))
        fig_pm.update_layout(height=260,margin=dict(l=10,r=10,t=40,b=10),paper_bgcolor='white')
        st.plotly_chart(fig_pm,use_container_width=True)
    with c2:
        st.markdown('| Program Gate | Status | Evidence |\n|---|---|---|\n' + ''.join(
            f"| {name} | {'PASS' if ok else 'RISK'} | {detail} |\n" for name,ok,detail in gates
        ))

    risks=[]
    if R['pack_margin_pct'] < 5:
        risks.append(('Battery sizing margin is below 5%', 'High', 'Increase gross pack or reduce design Wh/km'))
    if R['torque_margin'] < 8:
        risks.append(('Grade torque margin is tight', 'High', 'Adjust gear ratio or motor torque'))
    if R['V_sag_pct_dcfc'] > 5:
        risks.append(('DC fast-charge voltage sag may derate charger', 'Medium', 'Reduce DCIR or charge current'))
    if R['T_winding'] > 140:
        risks.append(('Motor winding temperature headroom is low', 'Medium', 'Improve cooling path / reduce continuous load'))

    if risks:
        st.markdown('**Risk Register**')
        st.markdown('| Risk | Severity | Mitigation |\n|---|---|---|\n' + ''.join(
            f"| {r} | {sev} | {mit} |\n" for r,sev,mit in risks
        ))
    else:
        st.markdown('<div class="rolebox">No immediate high/medium program risks detected for the current input set.</div>', unsafe_allow_html=True)

    high_count=sum(1 for _,sev,_ in risks if sev=='High')
    med_count=sum(1 for _,sev,_ in risks if sev=='Medium')
    launch_weeks=20 + high_count*2 + med_count
    st.markdown('<div class="rolebox">'
                f"Planning estimate: baseline 20 weeks + risk buffer = <b>{launch_weeks} weeks</b> from current readiness snapshot."
                '</div>', unsafe_allow_html=True)
