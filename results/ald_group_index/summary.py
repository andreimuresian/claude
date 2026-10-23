import json
rows = []
for f in ("results.txt", "jerez_light.txt", "cordoba_wg1.txt", "cordoba_buf.txt"):
    for l in open(f):
        if l.startswith("RESULT"):
            r = json.loads(l[7:])
            if r["design"] == "jerez" and not r.get("light"): continue
            if r["design"] == "cordoba" and r.get("wg_top") == 1.0: r["design"] = "cordoba_wg1.0"
            if r["design"] == "cordoba_buf": r["design"] = "cordoba_wg1.0_buffer200"
            rows.append(r)
with open("group_index_ALD.csv", "w") as f:
    f.write("design,wavelength_nm,T_ALD_nm,ALD_model,n_ALD,mesh,n_eff,ng_pm1nm,ng_pm2nm,IL_dB_per_cm,VpiL_Vcm\n")
    for r in rows:
        wl = 1310 if r["design"] == "jerez" else 1575
        f.write(f"{r['design']},{wl},{r['T_nm']},{r['model'] if r['T_nm'] else '-'},{r['n_ald']:.4f},{'light' if r.get('light') else 'fine'},"
                f"{r['neff']:.6f},{r['ng_1nm']:.5f},{r['ng_2nm']:.5f},{r['IL_dBcm']:.4f},{r['VpiL_Vcm']:.4f}\n")
        print(r["design"], r["T_nm"], r["model"], f"{r['neff']:.6f} ng {r['ng_1nm']:.5f}/{r['ng_2nm']:.5f} IL {r['IL_dBcm']:.4f} V {r['VpiL_Vcm']:.4f}")
