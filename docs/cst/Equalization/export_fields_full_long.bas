' Full equaliser with any section lengths (e.g. 10 + 5 + 5 mm): E-field and H-field exports, 0-130 GHz.
' Frequencies: 1..60 GHz every 1 GHz, 62..130 GHz every 2 GHz (monitors "e-field (f=N)" and "h-field (f=N)", excitation [1]).
' ONE file per region with all frequencies (first column = frequency in GHz). Coordinates from the project parameters:
'   L1: centre y = -BEND_RADIUS, buried metal z 0 .. EL_L (+z);  L2: y = +BEND_RADIUS, z EL_L-EL_L2 .. EL_L (-z);
'   L3: y = 3*BEND_RADIUS, z EL_L-EL_L3 .. EL_L (+z). Raised sections (50 um gap taper + TAPER_L straight) beyond the
'   buried ends; bend 1 centre (y 0, z EL_L+0.05+TAPER_L), bend 2 centre (y 2*BEND_RADIUS, z EL_L-EL_L2-0.05-TAPER_L).
' E: gap lines (buried x = MTX/2, raised x = CLAD_H+MTX/2) and 2D bend maps, as in the earlier runs.
' H: cross-sections (planes) around the signal electrode, for the current (loop integral of H) and the power flow:
'   buried: 3 planes in one cell at mid-length of each line (z, z+PITCH/3, z+2*PITCH/3), x -0.001..MTX+0.001;
'   raised: one plane at mid-length of each raised straight, x CLAD_H-0.001..CLAD_H+MTX+0.001;
'   bend apex (90 deg): plane through the bend centre, normal to the line;  all planes y = centre +/- 0.026, step 0.0005.
Option Explicit

Const F_MIN As Integer = 1
Const F_MAX As Integer = 130
Const EXC As String = "[1]"
Const EXPORT_E As Boolean = True
Const EXPORT_H As Boolean = True
Const EXPORT_BEND_MAPS As Boolean = True      ' E bend maps, ~480 MB each

Sub Main ()
    Dim outDir As String, br As Double, ws As Double, gp As Double, gp2 As Double, mtx As Double, clad As Double
    Dim l1 As Double, l2 As Double, l3 As Double, tl As Double, pitch As Double
    Dim dy As Double, dy2 As Double, xb As Double, xr As Double, zb1 As Double, zb2 As Double, z2s As Double, z3s As Double, hw As Double
    br = RestoreDoubleParameter("BEND_RADIUS"): ws = RestoreDoubleParameter("WS"): gp = RestoreDoubleParameter("GAP")
    gp2 = RestoreDoubleParameter("GAP2"): mtx = RestoreDoubleParameter("MTX"): clad = RestoreDoubleParameter("CLAD_H")
    l1 = RestoreDoubleParameter("EL_L"): l2 = RestoreDoubleParameter("EL_L2"): l3 = RestoreDoubleParameter("EL_L3")
    tl = RestoreDoubleParameter("TAPER_L"): pitch = RestoreDoubleParameter("PITCH")
    dy = ws / 2 + gp / 2: dy2 = ws / 2 + gp2 / 2: xb = mtx / 2: xr = clad + mtx / 2
    z2s = l1 - l2: z3s = l1 - l3: zb1 = l1 + 0.05 + tl: zb2 = z2s - 0.05 - tl: hw = 0.026

    outDir = GetProjectPath("Project") & "_field_exports\"
    On Error Resume Next
    MkDir outDir
    On Error GoTo 0

    If EXPORT_E Then
        '            name                      xmin xmax  ymin           ymax           zmin  zmax  step
        DoRegion outDir, "E", "L1_gap+",          xb, xb, -br + dy,       -br + dy,       0,    l1,   0.005
        DoRegion outDir, "E", "L1_gap-",          xb, xb, -br - dy,       -br - dy,       0,    l1,   0.005
        DoRegion outDir, "E", "L2_gap+",          xb, xb,  br + dy,        br + dy,       z2s,  l1,   0.005
        DoRegion outDir, "E", "L2_gap-",          xb, xb,  br - dy,        br - dy,       z2s,  l1,   0.005
        DoRegion outDir, "E", "L3_gap+",          xb, xb,  3 * br + dy,    3 * br + dy,   z3s,  l1,   0.005
        DoRegion outDir, "E", "L3_gap-",          xb, xb,  3 * br - dy,    3 * br - dy,   z3s,  l1,   0.005
        DoRegion outDir, "E", "L1_taper_gap+",    xr, xr, -br + dy2,      -br + dy2,      l1,   zb1,  0.005
        DoRegion outDir, "E", "L1_taper_gap-",    xr, xr, -br - dy2,      -br - dy2,      l1,   zb1,  0.005
        DoRegion outDir, "E", "L2_taper_end_gap+",   xr, xr, br + dy2,     br + dy2,      l1,   zb1,  0.005
        DoRegion outDir, "E", "L2_taper_end_gap-",   xr, xr, br - dy2,     br - dy2,      l1,   zb1,  0.005
        DoRegion outDir, "E", "L2_taper_start_gap+", xr, xr, br + dy2,     br + dy2,      zb2,  z2s,  0.005
        DoRegion outDir, "E", "L2_taper_start_gap-", xr, xr, br - dy2,     br - dy2,      zb2,  z2s,  0.005
        DoRegion outDir, "E", "L3_taper_gap+",    xr, xr,  3 * br + dy2,   3 * br + dy2,  zb2,  z3s,  0.005
        DoRegion outDir, "E", "L3_taper_gap-",    xr, xr,  3 * br - dy2,   3 * br - dy2,  zb2,  z3s,  0.005
        If EXPORT_BEND_MAPS Then
            DoRegion outDir, "E", "BEND1", xr, xr, -0.13,          0.13,           zb1 - 0.004, zb1 + 0.126, 0.001
            DoRegion outDir, "E", "BEND2", xr, xr,  2 * br - 0.13, 2 * br + 0.13,  zb2 - 0.126, zb2 + 0.004, 0.001
        End If
    End If

    If EXPORT_H Then
        Dim k As Integer, zm As Double, nm As String
        For k = 0 To 2
            zm = Int((l1 / 2) / pitch) * pitch + k * pitch / 3
            DoRegion outDir, "H", "H_L1_xs" & CStr(k), -0.001, mtx + 0.001, -br - hw, -br + hw, zm, zm, 0.0005
            zm = z2s + Int((l2 / 2) / pitch) * pitch + k * pitch / 3
            DoRegion outDir, "H", "H_L2_xs" & CStr(k), -0.001, mtx + 0.001, br - hw, br + hw, zm, zm, 0.0005
            zm = z3s + Int((l3 / 2) / pitch) * pitch + k * pitch / 3
            DoRegion outDir, "H", "H_L3_xs" & CStr(k), -0.001, mtx + 0.001, 3 * br - hw, 3 * br + hw, zm, zm, 0.0005
        Next k
        DoRegion outDir, "H", "H_raised_L1",    clad - 0.001, clad + mtx + 0.001, -br - hw,     -br + hw,     l1 + 0.05 + tl / 2, l1 + 0.05 + tl / 2, 0.0005
        DoRegion outDir, "H", "H_raised_L2end", clad - 0.001, clad + mtx + 0.001,  br - hw,      br + hw,     l1 + 0.05 + tl / 2, l1 + 0.05 + tl / 2, 0.0005
        DoRegion outDir, "H", "H_raised_L2start", clad - 0.001, clad + mtx + 0.001, br - hw,     br + hw,     z2s - 0.05 - tl / 2, z2s - 0.05 - tl / 2, 0.0005
        DoRegion outDir, "H", "H_raised_L3",    clad - 0.001, clad + mtx + 0.001,  3 * br - hw,  3 * br + hw, z3s - 0.05 - tl / 2, z3s - 0.05 - tl / 2, 0.0005
        DoRegion outDir, "H", "H_bend1_apex",   clad - 0.001, clad + mtx + 0.001,  0, 0,          zb1 + br - hw, zb1 + br + hw, 0.0005
        DoRegion outDir, "H", "H_bend2_apex",   clad - 0.001, clad + mtx + 0.001,  2 * br, 2 * br, zb2 - br - hw, zb2 - br + hw, 0.0005
    End If

    MsgBox "Field export finished: " & outDir & vbCrLf & "L1 z 0 .. " & l1 & ", L2 z " & z2s & " .. " & l1 & ", L3 z " & z3s & " .. " & l1 & _
           vbCrLf & "bend 1 centre z " & zb1 & ", bend 2 centre z " & zb2
End Sub

' Exports one region (E or H) for all frequencies and merges them into <outDir><name>.txt
Sub DoRegion (outDir As String, fld As String, name As String, _
              x0 As Double, x1 As Double, y0 As Double, y1 As Double, z0 As Double, z1 As Double, stp As Double)
    Dim f As Integer, item As String, tmp As String, merged As String
    Dim fin As Integer, fout As Integer, s As String, t As String, headerDone As Boolean

    merged = outDir & name & ".txt"
    tmp = outDir & "_tmp_export.txt"
    fout = FreeFile
    Open merged For Output As #fout
    Print #fout, "# region " & name & " (" & fld & "): x " & x0 & " .. " & x1 & ", y " & y0 & " .. " & y1 & _
                 ", z " & z0 & " .. " & z1 & " mm, step " & stp & " mm, excitation " & EXC
    headerDone = False

    For f = F_MIN To F_MAX
      If f <= 60 Or f Mod 2 = 0 Then
        If fld = "E" Then
            item = "2D/3D Results\E-Field\e-field (f=" & CStr(f) & ") " & EXC
        Else
            item = "2D/3D Results\H-Field\h-field (f=" & CStr(f) & ") " & EXC
        End If
        If SelectTreeItem(item) = False Then
            ReportWarningToWindow "Missing result: " & item
        Else
            With ASCIIExport
                .Reset
                .FileName tmp
                .SetFileType "txt"
                .Mode "FixedWidth"
                .Step stp
                .UseSubvolume True
                .SetSubvolume x0, x1, y0, y1, z0, z1
                .Execute
            End With

            fin = FreeFile
            Open tmp For Input As #fin
            Do While Not EOF(fin)
                Line Input #fin, s
                t = Trim(s)
                If Len(t) > 0 Then
                    If IsDataRow(t) Then
                        Print #fout, CStr(f) & vbTab & t
                    ElseIf Not headerDone And Left(t, 2) <> "--" Then
                        Print #fout, "f [GHz]" & vbTab & t
                        headerDone = True
                    End If
                End If
            Loop
            Close #fin
        End If
      End If
    Next f

    Close #fout
    On Error Resume Next
    Kill tmp
    On Error GoTo 0
End Sub

Function IsDataRow (t As String) As Boolean
    Dim c As String
    c = Left(t, 1)
    If c = "-" Or c = "+" Then c = Mid(t, 2, 1)
    IsDataRow = (InStr("0123456789.", c) > 0 And Len(c) = 1)
End Function
