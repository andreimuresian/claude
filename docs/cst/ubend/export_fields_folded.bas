' Folded line (3 straight lines + 2 U-bends), project "BASELINE - FULL EQUALIZER".
' Exports the E-field of monitors "e-field (f=N) [1]" (port 1 excitation), N = 1..60 GHz,
' and writes ONE file per region containing all frequencies (first column = frequency in GHz).
'
' Geometry (parameters of the run, mm): EL_L 2.7, EL_L2 = EL_L3 = 1.44, TAPER_L 0.22434,
' BEND_RADIUS 0.1025, WS 0.0347, GAP 0.00445, GAP2 0.0048, MTX 0.002, DEV_L 3.7.
'   Line 1: centre y = -0.1025, metal z 0 .. 2.7, raised taper 2.7 .. 2.97434, bend 1 beyond 2.97434
'   Line 2: centre y = +0.1025, metal z 1.26 .. 2.7, tapers 0.98566 .. 1.26 and 2.7 .. 2.97434
'   Line 3: centre y = +0.3075, metal z 1.26 .. 2.7 (port 2 at z = 2.7), taper 0.98566 .. 1.26
'   Bend 1: centre y = 0,     arc from z = 2.97434 towards +z, gap radii 0.08275 / 0.12225
'   Bend 2: centre y = 0.205, arc from z = 0.98566 towards -z, gap radii 0.08275 / 0.12225
' Gap centres: line centre +/- (WS/2 + GAP/2) = +/- 0.019575; tapers and bends +/- (WS/2 + GAP2/2 + 0.175 um) = 0.01975.
' x = 0.001 = mid-height of the buried electrodes; x = 0.0046 = mid-height of the raised ones.

Option Explicit

Const F_MIN As Integer = 1
Const F_MAX As Integer = 60
Const EXC As String = "[1]"          ' excitation: [1] = port 1
Const EXPORT_BENDS As Boolean = True ' bend maps, ~360 MB each (RF propagation only: bends do not modulate)
' Raised sections (tapers + bends): metal on top of the SiO2 cladding, x = CLAD_H .. CLAD_H+MTX = 0.0036 .. 0.0056,
' gap mid-height x = 0.0046. They need monitors reaching x = CLAD_H+MTX (field_monitors_ubend.bas, re-run).
' With the old monitors (x 0 .. MTX) these exports fail or come out empty.

Sub Main ()
    Dim outDir As String
    outDir = GetProjectPath("Project") & "_field_exports\"
    On Error Resume Next
    MkDir outDir
    On Error GoTo 0

    '                     name                 xmin    xmax    ymin       ymax       zmin   zmax   step
    ' Buried straight lines (metal x 0 .. MTX), gap centres = line centre +/- (WS/2+GAP/2)
    DoRegion outDir, "L1_gap+",             0.001,  0.001, -0.082925, -0.082925, 0,     2.70,  0.005
    DoRegion outDir, "L1_gap-",             0.001,  0.001, -0.122075, -0.122075, 0,     2.70,  0.005
    DoRegion outDir, "L2_gap+",             0.001,  0.001,  0.122075,  0.122075, 1.26,  2.70,  0.005
    DoRegion outDir, "L2_gap-",             0.001,  0.001,  0.082925,  0.082925, 1.26,  2.70,  0.005
    DoRegion outDir, "L3_gap+",             0.001,  0.001,  0.327075,  0.327075, 1.26,  2.70,  0.005
    DoRegion outDir, "L3_gap-",             0.001,  0.001,  0.287925,  0.287925, 1.26,  2.70,  0.005
    ' Raised tapers (x mid-height 0.0046), gap centres = line centre +/- 0.01975
    DoRegion outDir, "L1_taper_gap+",       0.0046, 0.0046, -0.08275,  -0.08275,  2.70,  2.975, 0.005
    DoRegion outDir, "L1_taper_gap-",       0.0046, 0.0046, -0.12225,  -0.12225,  2.70,  2.975, 0.005
    DoRegion outDir, "L2_taper_end_gap+",   0.0046, 0.0046,  0.12225,   0.12225,  2.70,  2.975, 0.005
    DoRegion outDir, "L2_taper_end_gap-",   0.0046, 0.0046,  0.08275,   0.08275,  2.70,  2.975, 0.005
    DoRegion outDir, "L2_taper_start_gap+", 0.0046, 0.0046,  0.12225,   0.12225,  0.985, 1.26,  0.005
    DoRegion outDir, "L2_taper_start_gap-", 0.0046, 0.0046,  0.08275,   0.08275,  0.985, 1.26,  0.005
    DoRegion outDir, "L3_taper_gap+",       0.0046, 0.0046,  0.32725,   0.32725,  0.985, 1.26,  0.005
    DoRegion outDir, "L3_taper_gap-",       0.0046, 0.0046,  0.28775,   0.28775,  0.985, 1.26,  0.005
    ' Raised U-bends (2D maps), gap radii 0.08275 / 0.12225 around the bend centre
    If EXPORT_BENDS Then DoRegion outDir, "BEND1", 0.0046, 0.0046, -0.13,  0.13,  2.97,  3.10,  0.001
    If EXPORT_BENDS Then DoRegion outDir, "BEND2", 0.0046, 0.0046,  0.075, 0.335, 0.86,  0.99,  0.001

    MsgBox "Field export finished: " & outDir
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
