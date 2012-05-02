##
## This file is part of the sigrok project.
##
## Copyright (C) 2012 Uwe Hermann <uwe@hermann-uwe.de>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
##

# ST STM32 JTAG protocol decoder

import sigrokdecode as srd

# JTAG debug port data registers (in IR[3:0]) and their sizes (in bits)
ir = {
    '1111': ['BYPASS', 1],  # Bypass register
    '1110': ['IDCODE', 32], # ID code register
    '1010': ['DPACC', 35],  # Debug port access register
    '1011': ['APACC', 35],  # Access port access register
    '1000': ['ABORT', 35],  # Abort register # TODO: 32 bits? Datasheet typo?
}

# ARM Cortex-M3 r1p1-01rel0 ID code
cm3_idcode = 0x3ba00477

# JTAG ID code in the STM32F10xxx BSC (boundary scan) TAP
jtag_idcode = {
    0x06412041: 'Low-density device, rev. A',
    0x06410041: 'Medium-density device, rev. A',
    0x16410041: 'Medium-density device, rev. B/Z/Y',
    0x06414041: 'High-density device, rev. A/Z/Y',
    0x06430041: 'XL-density device, rev. A',
    0x06418041: 'Connectivity-line device, rev. A/Z',
}

# ACK[2:0] in the DPACC/APACC registers
ack_val = {
    '000': 'Reserved',
    '001': 'WAIT',
    '010': 'OK/FAULT',
    '011': 'Reserved',
    '100': 'Reserved',
    '101': 'Reserved',
    '110': 'Reserved',
    '111': 'Reserved',
}

# 32bit debug port registers (addressed via A[3:2])
reg = {
    '00': 'Reserved', # Must be kept at reset value
    '01': 'DP CTRL/STAT',
    '10': 'DP SELECT',
    '11': 'DP RDBUFF',
}

# TODO: All start/end sample values in self.put() calls are bogus.

class Decoder(srd.Decoder):
    api_version = 1
    id = 'jtag_stm32'
    name = 'JTAG / STM32'
    longname = 'Joint Test Action Group / ST STM32'
    desc = 'ST STM32-specific JTAG protocol.'
    license = 'gplv2+'
    inputs = ['jtag']
    outputs = ['jtag_stm32']
    probes = []
    optional_probes = []
    options = {}
    annotations = [
        ['Text', 'Human-readable text'],
    ]

    def __init__(self, **kwargs):
        self.state = 'IDLE'
        # self.state = 'BYPASS'

    def start(self, metadata):
        # self.out_proto = self.add(srd.OUTPUT_PROTO, 'jtag_stm32')
        self.out_ann = self.add(srd.OUTPUT_ANN, 'jtag_stm32')

    def report(self):
        pass

    def handle_reg_bypass(self, bits):
        # TODO
        self.put(self.ss, self.es, self.out_ann, [0, ['BYPASS: ' + bits]])

    def handle_reg_idcode(self, bits):
        # TODO
        self.put(self.ss, self.es, self.out_ann,
                 [0, ['IDCODE: 0x%x' % int('0b' + bits, 2)]])

    # When transferring data IN:
    #   Bits[34:3] = DATA[31:0]: 32bit data to transfer (write request)
    #   Bits[2:1] = A[3:2]: 2-bit address of a debug port register
    #   Bits[0:0] = RnW: Read request (1) or write request (0)
    # When transferring data OUT:
    #   Bits[34:3] = DATA[31:0]: 32bit data which is read (read request)
    #   Bits[2:0] = ACK[2:0]: 3-bit acknowledge
    def handle_reg_dpacc(self, bits):
        self.put(self.ss, self.es, self.out_ann, [0, ['DPACC: ' + bits]])

        # TODO: When to use Data IN / Data OUT?

        # Data IN
        data, a, rnw = bits[:-3], bits[-3:-1], bits[-1]
        data_hex = '0x%x' % int('0b' + data, 2)
        r = 'Read request' if (rnw == '1') else 'Write request'
        s = 'DATA: %s, A: %s, RnW: %s' % (data_hex, reg[a], r)
        self.put(self.ss, self.es, self.out_ann, [0, [s]])

        # Data OUT
        data, ack = bits[:-3], bits[-3:]
        data_hex = '0x%x' % int('0b' + data, 2)
        ack_meaning = ack_val[ack]
        s = 'DATA: %s, ACK: %s' % (data_hex, ack_meaning)
        self.put(self.ss, self.es, self.out_ann, [0, [s]])

    # When transferring data IN:
    #   Bits[34:3] = DATA[31:0]: 32bit data to shift in (write request)
    #   Bits[2:1] = A[3:2]: 2-bit address (sub-address AP register)
    #   Bits[0:0] = RnW: Read request (1) or write request (0)
    # When transferring data OUT:
    #   Bits[34:3] = DATA[31:0]: 32bit data which is read (read request)
    #   Bits[2:0] = ACK[2:0]: 3-bit acknowledge
    def handle_reg_apacc(self, bits):
        self.put(self.ss, self.es, self.out_ann, [0, ['APACC: ' + bits]])

        # TODO: When to use Data IN / Data OUT?

        # Data IN
        data, a, rnw = bits[:-3], bits[-3:-1], bits[-1]
        data_hex = '0x%x' % int('0b' + data, 2)
        r = 'Read request' if (rnw == '1') else 'Write request'
        s = 'DATA: %s, A: %s, RnW: %s' % (data_hex, reg[a], r)
        self.put(self.ss, self.es, self.out_ann, [0, [s]])

        # Data OUT
        data, ack = bits[:-3], bits[-3:]
        data_hex = '0x%x' % int('0b' + data, 2)
        ack_meaning = ack_val[ack]
        s = 'DATA: %s, ACK: %s' % (data_hex, ack_meaning)
        self.put(self.ss, self.es, self.out_ann, [0, [s]])

    def handle_reg_abort(self, bits):
        # Bits[31:1]: reserved. Bit[0]: DAPABORT.
        a = '' if (bits[0] == '1') else 'No '
        s = 'DAPABORT = %s: %sDAP abort generated' % (bits[0], a)
        self.put(self.ss, self.es, self.out_ann, [0, [s]])

        # Warn if DAPABORT[31:1] contains non-zero bits.
        if (bits[:-1] != ('0' * 31)):
            self.put(self.ss, self.es, self.out_ann,
                     [0, ['WARNING: DAPABORT[31:1] reserved!']])

    def handle_reg_unknown(self, bits):
        self.put(self.ss, self.es, self.out_ann,
                 [0, ['Unknown instruction: ' % bits]]) # TODO

    def decode(self, ss, es, data):
        # Assumption: The right-most char in the 'val' bitstring is the LSB.
        cmd, val = data

        self.ss, self.es = ss, es

        # self.put(self.ss, self.es, self.out_ann, [0, [cmd + ' / ' + val]])

        # State machine
        if self.state == 'IDLE':
            # Wait until a new instruction is shifted into the IR register.
            if cmd != 'IR TDI':
                return
            # Switch to the state named after the instruction, or 'UNKNOWN'.
            self.state = ir.get(val[-4:], ['UNKNOWN', 0])[0]
            self.put(self.ss, self.es, self.out_ann, [0, ['IR: ' + self.state]])
        elif self.state in ('BYPASS'):
            # In these states we're interested in incoming bits (TDI).
            if cmd != 'DR TDI':
                return
            handle_reg = getattr(self, 'handle_reg_%s' % self.state.lower())
            handle_reg(val)
            self.state = 'IDLE'
        elif self.state in ('IDCODE', 'DPACC', 'APACC', 'ABORT', 'UNKNOWN'):
            # In these states we're interested in outgoing bits (TDO).
            # if cmd != 'DR TDO':
            if cmd not in ('DR TDI', 'DR TDO'):
                return
            handle_reg = getattr(self, 'handle_reg_%s' % self.state.lower())
            handle_reg(val)
            self.state = 'IDLE'
        else:
            raise Exception('Invalid state: %s' % self.state)
