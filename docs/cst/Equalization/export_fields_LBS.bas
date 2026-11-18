' L+B+S run (line 1 EL_L, raised taper + U-bend + raised taper, line 2 EL_L2), project "BASELINE - L+B+S".
' Exports the E-field of monitors "e-field (f=N) [1]" (port 1 excitation), N = 1..60 GHz every 1 GHz and 62..130 GHz every 2 GHz,
' ONE file per region with all frequencies (first column = frequency in GHz).
' Coordinates are computed from the project parameters (read from the open project):
'   line 1: centre y = -BEND_RADIUS, buried metal z 0 .. EL_L, RF along +z (port 1 at z = 0)
'   line 2: centre y = +BEND_RADIUS, buried metal z EL_L-EL_L2 .. EL_L, RF along -z (port 2 at z = EL_L-EL_L2)
'   buried gaps: y = centre +/- (WS/2 + GAP/2), x = MTX/2
'   raised tapers z EL_L .. EL_L+0.05+TAPER_L, gaps y = centre +/- (WS/2 + GAP2/2 + 0.000175), x = CLAD_H + MTX/2
'   U-bend: centre y = 0, arc from z = EL_L+0.05+TAPER_L towards +z, 2D map at x = CLAD_H + MTX/2
' With this run's parameters: EL_L 2.16, EL_L2 1.08 -> line 1 z 0 .. 2.16, line 2 z 1.08 .. 2.16,
'   tapers z 2.16 .. 2.43434, bend map y -0.13 .. 0.13, z 2.43 .. 2.56.
' The raised regions (tapers, bend) need monitors reaching x = CLAD_H+MTX; set EXPORT_RAISED = False otherwise.

Option Explicit

Const F_MIN As Integer = 1
Const F_MAX As Integer = 130       ' monitors: every 1 GHz up to 60, every 2 GHz above (field_monitors_130GHz.bas)
Const EXC As String = "[1]"          ' excitation: [1] = port 1
Const STP As Double = 0.005          ' lines
Const STP_BEND As Double = 0.001     ' bend map
Const EXPORT_RAISED As Boolean = True

Sub Main ()
    Dim outDir As String, br As Double, ws As Double, gp As Double, gp2 As Double, mtx As Double, clad As Double
    Dim ell As Double, ell2 As Double, tl As Double, dy As Double, dy2 As Double, xb As Double, xr As Double, zb As Double
    br   = RestoreDoubleParameter("BEND_RADIUS")
    ws   = RestoreDoubleParameter("WS")
    gp   = RestoreDoubleParameter("GAP")
    gp2  = RestoreDoubleParameter("GAP2")
    mtx  = RestoreDoubleParameter("MTX")
    clad = RestoreDoubleParameter("CLAD_H")
    ell  = RestoreDoubleParameter("EL_L")
    ell2 = RestoreDoubleParameter("EL_L2")
    tl   = RestoreDoubleParameter("TAPER_L")
    dy  = ws / 2 + gp / 2
    dy2 = ws / 2 + gp2 / 2 + 0.000175
    xb = mtx / 2                     ' mid-height of the buried electrodes
    xr = clad + mtx / 2              ' mid-height of the raised electrodes
    zb = ell + 0.05 + tl             ' start of the arc

    outDir = GetProjectPath("Project") & "_field_exports\"
    On Error Resume Next
    MkDir outDir
    On Error GoTo 0

    '                          name             xmin xmax  ymin       ymax       zmin        zmax        step
    DoRegion outDir, "L1_gap+",       xb, xb, -br + dy,  -br + dy,  0,          ell,        STP
    DoRegion outDir, "L1_gap-",       xb, xb, -br - dy,  -br - dy,  0,          ell,        STP
    DoRegion outDir, "L2_gap+",       xb, xb,  br + dy,   br + dy,  ell - ell2, ell,        STP
    DoRegion outDir, "L2_gap-",       xb, xb,  br - dy,   br - dy,  ell - ell2, ell,        STP
    If EXPORT_RAISED Then
        DoRegion outDir, "L1_taper_gap+", xr, xr, -br + dy2, -br + dy2, ell, zb, STP
        DoRegion outDir, "L1_taper_gap-", xr, xr, -br - dy2, -br - dy2, ell, zb, STP
        DoRegion outDir, "L2_taper_gap+", xr, xr,  br + dy2,  br + dy2, ell, zb, STP
        DoRegion outDir, "L2_taper_gap-", xr, xr,  br - dy2,  br - dy2, ell, zb, STP
        DoRegion outDir, "BEND",          xr, xr, -0.13, 0.13, zb - 0.005, zb + 0.125, STP_BEND
    End If

    MsgBox "Field export finished: " & outDir & vbCrLf & _
           "line 1 z 0 .. " & ell & ", line 2 z " & (ell - ell2) & " .. " & ell & ", arc from z " & zb
End Sub

' Exports one region for all frequencies and merges them into <outDir><name>.txt
Sub DoRegion (outDir As String, name As String, _
              x0 As Double, x1 As Double, y0 As Double, y1 As Double, z0 As Double, z1 As Double, stp As Double)
    Dim f As Integer, item As String, tmp As String, merged As String
    Dim fin As Integer, fout As Integer, s As String, t As String, headerDone As Boolean

    merged = outDir & name & ".txt"
    tmp = outDir & "_tmp_export.txt"
    fout = FreeFile
    Open merged For Output As #fout
    Print #fout, "# region " & name & ": x " & x0 & " .. " & x1 & ", y " & y0 & " .. " & y1 & _
                 ", z " & z0 & " .. " & z1 & " mm, step " & stp & " mm, excitation " & EXC
    headerDone = False

    For f = F_MIN To F_MAX
      If f <= 60 Or f Mod 2 = 0 Then
        item = "2D/3D Results\E-Field\e-field (f=" & CStr(f) & ") " & EXC
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
                        Print #fout, CStr(f) & vbTab & t                       ' data row: f [GHz] then CST columns
                    ElseIf Not headerDone And Left(t, 2) <> "--" Then
                        Print #fout, "f [GHz]" & vbTab & t                     ' column titles, once
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

' True for a numeric data row ("0.001 ...", "-0.08 ..."), false for titles and the dashed separator.
' Character test instead of IsNumeric, so the decimal point is read the same in every Windows locale.
Function IsDataRow (t As String) As Boolean
    Dim c As String
    c = Left(t, 1)
    If c = "-" Or c = "+" Then c = Mid(t, 2, 1)
    IsDataRow = (InStr("0123456789.", c) > 0 And Len(c) = 1)
End Function
