' Single-bend run (20 um buried stubs at the ports, vertical step, 50 um gap taper, TAPER_L raised straight, U-bend):
' E-field and H-field exports, 0-130 GHz (1..60 GHz every 1 GHz, 62..130 GHz every 2 GHz), excitation [1].
' Frequency loop OUTSIDE, regions inside: each field monitor is loaded once per frequency (much faster than region-first).
' ONE file per region with all frequencies (first column = frequency in GHz).
' Coordinates from the project parameters: line 1 (y = -BEND_RADIUS) buried z 0 .. EL_L, line 2 (y = +BEND_RADIUS) buried
' z EL_L-EL_L2 .. EL_L, raised sections EL_L .. EL_L+0.05+TAPER_L on both sides, arc centre (y 0, z EL_L+0.05+TAPER_L).
' The message box at the end prints EL_L and EL_L2: check them against the model.
' Planes (E AND H at the same positions, step 0.5 um, y = line centre +/- 0.026, i.e. signal, both gaps and part of the grounds):
'   stub    : middle of each buried stub, x -0.001 .. MTX+0.001
'   A, M, B : raised straight just after the gap taper (+10 um), at mid-length, just before the arc (-10 um), each side,
'             x CLAD_H-0.001 .. CLAD_H+MTX+0.001
'   apex    : plane through the arc centre normal to the line (y = 0), z = centre + BEND_RADIUS +/- 0.026
' Lines (E only, optional): raised gap lines on both sides; 2D bend map (optional, ~480 MB).
' The planes must lie inside the monitors (E and H monitors with x up to CLAD_H+MTX and down to 0 / -0.001).
Option Explicit

Const F_MAX As Integer = 130
Const EXC As String = "[1]"
Const EXPORT_LINES As Boolean = True
Const EXPORT_BEND_MAP As Boolean = True
Const NMAX As Integer = 40

Dim nR As Integer
Dim rName(NMAX) As String, rFld(NMAX) As String, rBox(NMAX, 6) As Double, rDone(NMAX) As Boolean

Sub AddR (fld As String, name As String, x0 As Double, x1 As Double, y0 As Double, y1 As Double, z0 As Double, z1 As Double, stp As Double)
    rName(nR) = name: rFld(nR) = fld
    rBox(nR, 0) = x0: rBox(nR, 1) = x1: rBox(nR, 2) = y0: rBox(nR, 3) = y1: rBox(nR, 4) = z0: rBox(nR, 5) = z1: rBox(nR, 6) = stp
    nR = nR + 1
End Sub

Sub Main ()
    Dim outDir As String, br As Double, ws As Double, gp2 As Double, mtx As Double, clad As Double, l1 As Double, l2 As Double, tl As Double
    Dim dy2 As Double, xr As Double, zb As Double, hw As Double, xb0 As Double, xb1 As Double, xr0 As Double, xr1 As Double
    Dim zs1 As Double, zs2 As Double, zPa As Double, zPm As Double, zPb As Double, sd As Integer, ys As Double, tag As String
    br = RestoreDoubleParameter("BEND_RADIUS"): ws = RestoreDoubleParameter("WS"): gp2 = RestoreDoubleParameter("GAP2")
    mtx = RestoreDoubleParameter("MTX"): clad = RestoreDoubleParameter("CLAD_H"): tl = RestoreDoubleParameter("TAPER_L")
    l1 = RestoreDoubleParameter("EL_L"): l2 = RestoreDoubleParameter("EL_L2")
    dy2 = ws / 2 + gp2 / 2: xr = clad + mtx / 2: zb = l1 + 0.05 + tl: hw = 0.026
    xb0 = -0.001: xb1 = mtx + 0.001: xr0 = clad - 0.001: xr1 = clad + mtx + 0.001
    zs1 = l1 / 2: zs2 = (l1 - l2) + l2 / 2: zPa = l1 + 0.06: zPm = l1 + 0.05 + tl / 2: zPb = zb - 0.01
    nR = 0
    For sd = 1 To 2
        If sd = 1 Then
            ys = -br: tag = "1"
        Else
            ys = br: tag = "2"
        End If
        If sd = 1 Then
            AddR "E", "E_stub1", xb0, xb1, ys - hw, ys + hw, zs1, zs1, 0.0005: AddR "H", "H_stub1", xb0, xb1, ys - hw, ys + hw, zs1, zs1, 0.0005
        Else
            AddR "E", "E_stub2", xb0, xb1, ys - hw, ys + hw, zs2, zs2, 0.0005: AddR "H", "H_stub2", xb0, xb1, ys - hw, ys + hw, zs2, zs2, 0.0005
        End If
        AddR "E", "E_A" & tag, xr0, xr1, ys - hw, ys + hw, zPa, zPa, 0.0005: AddR "H", "H_A" & tag, xr0, xr1, ys - hw, ys + hw, zPa, zPa, 0.0005
        AddR "E", "E_M" & tag, xr0, xr1, ys - hw, ys + hw, zPm, zPm, 0.0005: AddR "H", "H_M" & tag, xr0, xr1, ys - hw, ys + hw, zPm, zPm, 0.0005
        AddR "E", "E_B" & tag, xr0, xr1, ys - hw, ys + hw, zPb, zPb, 0.0005: AddR "H", "H_B" & tag, xr0, xr1, ys - hw, ys + hw, zPb, zPb, 0.0005
        If EXPORT_LINES Then
            AddR "E", "L" & tag & "_taper_gap+", xr, xr, ys + dy2, ys + dy2, l1, zb, 0.005
            AddR "E", "L" & tag & "_taper_gap-", xr, xr, ys - dy2, ys - dy2, l1, zb, 0.005
        End If
    Next sd
    AddR "E", "E_apex", xr0, xr1, 0, 0, zb + br - hw, zb + br + hw, 0.0005: AddR "H", "H_apex", xr0, xr1, 0, 0, zb + br - hw, zb + br + hw, 0.0005
    If EXPORT_BEND_MAP Then AddR "E", "BEND", xr, xr, -0.13, 0.13, zb - 0.005, zb + 0.125, 0.001

    outDir = GetProjectPath("Project") & "_field_exports\"
    On Error Resume Next
    MkDir outDir
    On Error GoTo 0
    Dim k As Integer, fo As Integer
    For k = 0 To nR - 1
        fo = FreeFile: Open outDir & rName(k) & ".txt" For Output As #fo
        Print #fo, "# region " & rName(k) & " (" & rFld(k) & "): x " & rBox(k, 0) & " .. " & rBox(k, 1) & ", y " & rBox(k, 2) & " .. " & rBox(k, 3) & _
                   ", z " & rBox(k, 4) & " .. " & rBox(k, 5) & " mm, step " & rBox(k, 6) & " mm, excitation " & EXC
        Close #fo: rDone(k) = False
    Next k

    Dim f As Integer, q As Integer, fld As String, item As String, ok As Boolean
    For f = 1 To F_MAX
      If f <= 60 Or f Mod 2 = 0 Then
        For q = 0 To 1
            If q = 0 Then
                fld = "E": item = "2D/3D Results\E-Field\e-field (f=" & CStr(f) & ") " & EXC
            Else
                fld = "H": item = "2D/3D Results\H-Field\h-field (f=" & CStr(f) & ") " & EXC
            End If
            ok = SelectTreeItem(item)
            If Not ok Then ReportWarningToWindow "Missing result: " & item
            For k = 0 To nR - 1
                If ok And rFld(k) = fld Then ExportOne outDir, k, f
            Next k
        Next q
      End If
    Next f
    MsgBox "Field export finished: " & outDir & vbCrLf & "EL_L = " & l1 & ", EL_L2 = " & l2 & ", arc centre z = " & zb & vbCrLf & _
           "planes A / M / B at z = " & zPa & " / " & zPm & " / " & zPb & ", stubs at z = " & zs1 & " / " & zs2
End Sub

' Exports region k at frequency f (the field result is already selected) and appends it to <outDir><name>.txt
Sub ExportOne (outDir As String, k As Integer, f As Integer)
    Dim tmp As String, fin As Integer, fout As Integer, s As String, t As String
    tmp = outDir & "_tmp_export.txt"
    With ASCIIExport
        .Reset
        .FileName tmp
        .SetFileType "txt"
        .Mode "FixedWidth"
        .Step rBox(k, 6)
        .UseSubvolume True
        .SetSubvolume rBox(k, 0), rBox(k, 1), rBox(k, 2), rBox(k, 3), rBox(k, 4), rBox(k, 5)
        .Execute
    End With
    fout = FreeFile: Open outDir & rName(k) & ".txt" For Append As #fout
    fin = FreeFile: Open tmp For Input As #fin
    Do While Not EOF(fin)
        Line Input #fin, s
        t = Trim(s)
        If Len(t) > 0 Then
            If IsDataRow(t) Then
                Print #fout, CStr(f) & vbTab & t
            ElseIf Not rDone(k) And Left(t, 2) <> "--" Then
                Print #fout, "f [GHz]" & vbTab & t
                rDone(k) = True
            End If
        End If
    Loop
    Close #fin: Close #fout
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
